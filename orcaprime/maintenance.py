"""Cópias consistentes na abertura, mantendo até sete dias locais."""
from datetime import date
from contextlib import closing, contextmanager
import os
import sqlite3
import tempfile
from pathlib import Path
from dataclasses import dataclass
import json
import shutil
import sys
import zipfile
import zlib
import re

ARCHIVE_MEMBER='orcaprime.db'
MAX_DATABASE_BYTES=2*1024**3
MAX_ARCHIVE_BYTES=1024**3


@contextmanager
def _backup_lock(folder):
    """Serialize writers to a daily filename across threads and processes."""
    with open(folder/'.orcaprime-backup.lock','a+b') as lock:
        if os.name=='nt':
            import msvcrt
            # Windows permits locking beyond EOF; never read an already locked byte.
            lock.seek(0)
            msvcrt.locking(lock.fileno(),msvcrt.LK_LOCK,1)
            try:yield
            finally:
                lock.seek(0)
                msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
        else:
            import fcntl
            fcntl.flock(lock.fileno(),fcntl.LOCK_EX)
            try:yield
            finally:fcntl.flock(lock.fileno(),fcntl.LOCK_UN)


@dataclass(frozen=True)
class BackupResult:
    local_path: Path
    cloud_path: Path | None = None
    cloud_error: str = ''


def backup_settings(store):
    with store.connect() as db:
        row=db.execute("SELECT value FROM meta WHERE key='backup_settings'").fetchone()
    try: value=json.loads(row[0]) if row else {}
    except (ValueError,TypeError):value={}
    if not isinstance(value,dict):value={}
    retention=value.get('retention',7)
    if type(retention) is not int or not 1<=retention<=365:retention=7
    folder=value.get('cloud_folder','')
    return {'retention':retention,'cloud_folder':folder if isinstance(folder,str) else ''}


def save_backup_settings(store,retention=7,cloud_folder=''):
    if type(retention) is not int or not 1<=retention<=365:raise ValueError('Informe entre 1 e 365 cópias.')
    cloud_folder=str(cloud_folder).strip()
    with store.connect() as db:
        db.execute('INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)',
                   ('backup_settings',json.dumps({'retention':retention,'cloud_folder':cloud_folder})))


def default_backup_dir(store):
    # Installed EXE lives under the current user's writable LocalAppData/Programs.
    return (Path(sys.executable).resolve().parent if getattr(sys,'frozen',False)
            else store.path.parent)/'backup'


def _checked_archive(path):
    path=Path(path)
    if path.stat().st_size>MAX_ARCHIVE_BYTES:raise ValueError('Arquivo de backup grande demais.')
    with zipfile.ZipFile(path) as archive:
        members=archive.infolist()
        if len(members)!=1 or members[0].filename!=ARCHIVE_MEMBER or members[0].is_dir():
            raise ValueError('O ZIP deve conter somente orcaprime.db.')
        member=members[0]
        if member.file_size==0 or member.compress_size==0 or member.file_size>MAX_DATABASE_BYTES or member.compress_size>MAX_ARCHIVE_BYTES:
            raise ValueError('Banco de backup grande demais.')
        if member.flag_bits & 1:raise ValueError('ZIP criptografado não é aceito.')
        return member


def _extract_archive(path,destination):
    _checked_archive(path)
    with zipfile.ZipFile(path) as archive, archive.open(ARCHIVE_MEMBER) as src, open(destination,'wb') as dst:
        copied=0
        while chunk:=src.read(1024*1024):
            copied+=len(chunk)
            if copied>MAX_DATABASE_BYTES:raise ValueError('Banco de backup grande demais.')
            dst.write(chunk)
    if not _valid(Path(destination)):raise ValueError('Banco de backup inválido.')


def _extract_checked_archive(path,destination):
    try:
        _extract_archive(path,destination)
    except (zlib.error, zipfile.BadZipFile, EOFError, RuntimeError) as error:
        raise ValueError('Backup compactado corrompido.') from error


def _copy_to_cloud(source,folder):
    folder=Path(folder).expanduser()
    folder.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.orcaprime-cloud-',suffix='.tmp',dir=folder)
    os.close(fd);temporary=Path(name)
    try:
        shutil.copyfile(source,temporary)
        with tempfile.TemporaryDirectory() as dirname:
            _extract_checked_archive(temporary,Path(dirname)/ARCHIVE_MEMBER)
        temporary.replace(folder/source.name)
        return folder/source.name
    finally:temporary.unlink(missing_ok=True)


def _prune(folder,retention):
    copies=[]
    for path in folder.glob('orcaprime-*.zip'):
        match=re.fullmatch(r'orcaprime-(\d{4}-\d{2}-\d{2})\.zip',path.name)
        if match:
            try:date.fromisoformat(match.group(1))
            except ValueError:continue
            copies.append(path)
    copies.sort()
    for path in copies[:-retention]:path.unlink()


def run_daily_backup(store,backup_dir=None,force=False):
    settings=backup_settings(store)
    folder=Path(backup_dir) if backup_dir is not None else default_backup_dir(store)
    folder.mkdir(parents=True,exist_ok=True)
    with _backup_lock(folder):
        destination=folder/('orcaprime-'+date.today().isoformat()+'.zip')
        good=False
        if destination.exists() and not force:
            try:
                with tempfile.TemporaryDirectory() as dirname:
                    _extract_checked_archive(destination,Path(dirname)/ARCHIVE_MEMBER)
                good=True
            except (OSError,ValueError,zipfile.BadZipFile,RuntimeError,OverflowError):pass
        if not good:
            fd,name=tempfile.mkstemp(prefix='.orcaprime-backup-',suffix='.db',dir=folder)
            os.close(fd);snapshot=Path(name)
            fd,name=tempfile.mkstemp(prefix='.orcaprime-backup-',suffix='.tmp',dir=folder)
            os.close(fd);temporary=Path(name)
            try:
                store.backup(snapshot)
                if not snapshot.stat().st_size or not _valid(snapshot):raise ValueError('A cópia não passou na verificação de integridade.')
                with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
                    archive.write(snapshot,ARCHIVE_MEMBER)
                with tempfile.TemporaryDirectory() as dirname:
                    _extract_checked_archive(temporary,Path(dirname)/ARCHIVE_MEMBER)
                temporary.replace(destination)
            finally:
                snapshot.unlink(missing_ok=True);temporary.unlink(missing_ok=True)
        _prune(folder,settings['retention'])
        cloud_path=None;cloud_error=''
        if settings['cloud_folder']:
            try:
                cloud_path=_copy_to_cloud(destination,settings['cloud_folder'])
                _prune(cloud_path.parent,settings['retention'])
            except (OSError,ValueError,zipfile.BadZipFile,RuntimeError) as error:cloud_error=str(error)
        return BackupResult(destination,cloud_path,cloud_error)


def restore_backup(store,source):
    source=Path(source)
    if source.suffix.lower()=='.db':
        store.restore(source)
        return
    if source.suffix.lower()!='.zip':raise ValueError('Selecione um backup ZIP ou DB.')
    try:
        with tempfile.TemporaryDirectory(dir=store.path.parent) as dirname:
            extracted=Path(dirname)/ARCHIVE_MEMBER
            _extract_checked_archive(source,extracted)
            store.restore(extracted)
    except (OSError,zipfile.BadZipFile,RuntimeError,OverflowError,EOFError) as error:
        raise ValueError('Backup ZIP inválido ou inacessível. O banco atual foi preservado.') from error


def _valid(path):
    try:
        with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)) as db:
            if db.execute('PRAGMA integrity_check').fetchone()!=('ok',):return False
            from .backup_validation import validate_database
            validate_database(db)
        return True
    except (sqlite3.Error,ValueError,TypeError,KeyError,OSError):return False


def daily_backup(store):
    folder=store.path.parent/'backups-automaticos';folder.mkdir(exist_ok=True)
    destination=folder/('orcaprime-auto-'+date.today().isoformat()+'.db')
    if not destination.exists() or not _valid(destination):
        fd,name=tempfile.mkstemp(prefix='backup-',suffix='.tmp',dir=folder);os.close(fd);temporary=Path(name)
        try:
            store.backup(temporary)
            if not _valid(temporary):raise ValueError('A cópia automática não passou na verificação de integridade.')
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
    copies=sorted(folder.glob('orcaprime-auto-????-??-??.db'))
    for path in copies[:-7]:path.unlink()
    return destination
