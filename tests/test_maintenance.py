import pytest
from orcaprime.storage import Store
from orcaprime.maintenance import daily_backup
from orcaprime.maintenance import run_daily_backup, restore_backup, save_backup_settings, backup_settings
import zipfile
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor
import threading
import time


def test_daily_backup_repairs_incomplete_copy(tmp_path):
    store=Store(tmp_path/'app.db');store.save_customer({'name':'Cliente'})
    copy=daily_backup(store);copy.write_bytes(b'backup incompleto')
    assert daily_backup(store)==copy
    recovered=Store(copy)
    assert recovered.list_customers()[0]['name']=='Cliente'


def test_failed_backup_never_creates_daily_destination(tmp_path,monkeypatch):
    store=Store(tmp_path/'app.db')
    def broken(path):
        path.write_bytes(b'parcial')
        raise OSError('disco cheio')
    monkeypatch.setattr(store,'backup',broken)
    with pytest.raises(OSError):daily_backup(store)
    assert not list((tmp_path/'backups-automaticos').glob('*.db'))
    assert not list((tmp_path/'backups-automaticos').glob('*.tmp'))


def test_compressed_backup_validates_and_restores(tmp_path):
    source=Store(tmp_path/'source.db');source.save_customer({'name':'Recovered'})
    result=run_daily_backup(source,backup_dir=tmp_path/'backup')
    assert result.local_path.suffix=='.zip'
    with zipfile.ZipFile(result.local_path) as archive:
        assert archive.namelist()==['orcaprime.db']
        assert archive.testzip() is None
    target=Store(tmp_path/'target.db');target.save_customer({'name':'Keep'})
    restore_backup(target,result.local_path)
    assert target.list_customers()[0]['name']=='Recovered'
    assert list(tmp_path.glob('antes-restauracao-*.db'))


def test_corrupt_zip_and_extra_archive_entries_preserve_database(tmp_path):
    target=Store(tmp_path/'target.db');target.save_customer({'name':'Keep'})
    bad=tmp_path/'bad.zip';bad.write_bytes(b'not zip')
    with pytest.raises(ValueError):restore_backup(target,bad)
    with zipfile.ZipFile(bad,'w') as archive:
        archive.writestr('orcaprime.db',b'not a database')
        archive.writestr('../escape.db',b'evil')
    with pytest.raises(ValueError):restore_backup(target,bad)
    assert target.list_customers()[0]['name']=='Keep'
    assert not (tmp_path/'escape.db').exists()


def test_cloud_failure_does_not_lose_local_backup(tmp_path,monkeypatch):
    source=Store(tmp_path/'source.db')
    save_backup_settings(source,retention=3,cloud_folder=str(tmp_path/'cloud'))
    from orcaprime import maintenance
    def broken(*args,**kwargs): raise OSError('offline')
    monkeypatch.setattr(maintenance,'_copy_to_cloud',broken)
    result=run_daily_backup(source,backup_dir=tmp_path/'backup')
    assert result.local_path.is_file()
    assert 'offline' in result.cloud_error
    assert backup_settings(source)['retention']==3


def test_retention_removes_only_old_validly_named_versions(tmp_path):
    source=Store(tmp_path/'source.db');folder=tmp_path/'backup';folder.mkdir()
    save_backup_settings(source,retention=2)
    for offset in (3,2,1):
        old=folder/f"orcaprime-{(date.today()-timedelta(days=offset)).isoformat()}.zip"
        old.write_bytes(b'old')
    unrelated=folder/'my-backup.zip';unrelated.write_bytes(b'other')
    run_daily_backup(source,backup_dir=folder)
    assert len(list(folder.glob('orcaprime-????-??-??.zip')))==2
    assert unrelated.exists()


def test_old_db_restore_still_supported(tmp_path):
    source=Store(tmp_path/'source.db');source.save_customer({'name':'Old'})
    target=Store(tmp_path/'target.db')
    restore_backup(target,source.path)
    assert target.list_customers()[0]['name']=='Old'


def test_invalid_daily_zip_is_replaced_by_valid_snapshot(tmp_path):
    source=Store(tmp_path/'source.db');source.save_customer({'name':'Latest'})
    folder=tmp_path/'backup';folder.mkdir()
    destination=folder/('orcaprime-'+date.today().isoformat()+'.zip')
    with zipfile.ZipFile(destination,'w') as archive:archive.writestr('orcaprime.db',b'bad database')
    result=run_daily_backup(source,backup_dir=folder)
    target=Store(tmp_path/'target.db');restore_backup(target,result.local_path)
    assert target.list_customers()[0]['name']=='Latest'


def test_forced_backup_replaces_today_with_current_data(tmp_path):
    source=Store(tmp_path/'source.db');folder=tmp_path/'backup'
    first=run_daily_backup(source,backup_dir=folder)
    source.save_customer({'name':'Recent'})
    second=run_daily_backup(source,backup_dir=folder,force=True)
    assert first.local_path==second.local_path
    target=Store(tmp_path/'target.db');restore_backup(target,second.local_path)
    assert target.list_customers()[0]['name']=='Recent'


def test_failed_forced_backup_keeps_previous_valid_version(tmp_path,monkeypatch):
    source=Store(tmp_path/'source.db');first=run_daily_backup(source,backup_dir=tmp_path/'backup')
    previous=first.local_path.read_bytes()
    def broken(path):
        path.write_bytes(b'')
        raise OSError('disk full')
    monkeypatch.setattr(source,'backup',broken)
    with pytest.raises(OSError,match='disk full'):
        run_daily_backup(source,backup_dir=tmp_path/'backup',force=True)
    assert first.local_path.read_bytes()==previous
    assert not list((tmp_path/'backup').glob('.orcaprime-backup-*.tmp'))


def test_cloud_retention_only_removes_owned_daily_names(tmp_path):
    source=Store(tmp_path/'source.db');folder=tmp_path/'backup';cloud=tmp_path/'cloud';cloud.mkdir()
    save_backup_settings(source,retention=2,cloud_folder=str(cloud))
    for offset in (3,2,1):
        (cloud/f"orcaprime-{(date.today()-timedelta(days=offset)).isoformat()}.zip").write_bytes(b'old')
    unrelated=cloud/'report.zip';unrelated.write_bytes(b'keep')
    result=run_daily_backup(source,backup_dir=folder)
    assert result.cloud_error==''
    assert len(list(cloud.glob('orcaprime-????-??-??.zip')))==2
    assert unrelated.read_bytes()==b'keep'


def test_competing_writers_are_serialized(tmp_path,monkeypatch):
    source=Store(tmp_path/'source.db');folder=tmp_path/'backup'
    original=source.backup
    guard=threading.Lock();active=0;peak=0
    def measured(path):
        nonlocal active,peak
        with guard:
            active+=1;peak=max(peak,active)
        try:
            time.sleep(0.04)
            original(path)
        finally:
            with guard:active-=1
    monkeypatch.setattr(source,'backup',measured)
    with ThreadPoolExecutor(max_workers=2) as workers:
        results=list(workers.map(lambda _:run_daily_backup(source,backup_dir=folder,force=True),range(2)))
    assert peak==1
    target=Store(tmp_path/'restored.db');restore_backup(target,results[0].local_path)


def test_corrupted_deflate_is_repaired(tmp_path):
    import struct
    from orcaprime.maintenance import run_daily_backup
    store=Store(tmp_path/'app.db')
    destination=run_daily_backup(store).local_path
    raw=bytearray(destination.read_bytes())
    name_size,extra_size=struct.unpack_from('<HH',raw,26)
    raw[30+name_size+extra_size]=255
    destination.write_bytes(raw)
    assert run_daily_backup(store).local_path==destination
