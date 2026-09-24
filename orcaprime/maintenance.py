"""Cópias consistentes na abertura, mantendo até sete dias locais."""
from datetime import date
from contextlib import closing
import os
import sqlite3
import tempfile
from pathlib import Path


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
