from pathlib import Path

import pytest

from orcaprime.backup_scheduler import backup_job
from orcaprime.maintenance import save_backup_settings
from orcaprime.backup_scheduler import read_backup_status
import json
from orcaprime.storage import Store


def test_headless_job_does_not_create_missing_database(tmp_path):
    with pytest.raises(FileNotFoundError):backup_job(tmp_path)
    assert not (tmp_path/'orcaprime.db').exists()
    assert 'Banco OrçaPrime' in read_backup_status(tmp_path)['error']


def test_headless_job_creates_zip_without_gui(tmp_path):
    store=Store(tmp_path/'orcaprime.db');store.save_customer({'name':'Scheduled'})
    result=backup_job(tmp_path)
    assert result.local_path.is_file()
    assert result.local_path.parent==tmp_path/'backup'
    assert read_backup_status(tmp_path)['state']=='ok'


def test_headless_run_refreshes_today_snapshot(tmp_path):
    store=Store(tmp_path/'orcaprime.db')
    backup_job(tmp_path)
    store.save_customer({'name':'New today'})
    result=backup_job(tmp_path)
    from orcaprime.maintenance import restore_backup
    target=Store(tmp_path/'target.db');restore_backup(target,result.local_path)
    assert target.list_customers()[0]['name']=='New today'


def test_headless_job_reports_secondary_failure_after_local_success(tmp_path,monkeypatch):
    store=Store(tmp_path/'orcaprime.db')
    save_backup_settings(store,cloud_folder=str(tmp_path/'cloud'))
    from orcaprime import maintenance
    monkeypatch.setattr(maintenance,'_copy_to_cloud',lambda *_: (_ for _ in ()).throw(OSError('offline')))
    with pytest.raises(RuntimeError,match='Backup local salvo.*offline'):backup_job(tmp_path)
    assert list((tmp_path/'backup').glob('*.zip'))
    status=read_backup_status(tmp_path)
    assert status['state']=='partial' and 'offline' in status['error']


def test_installer_schedule_is_interactive_user_and_recoverable():
    script=(Path(__file__).resolve().parents[1]/'installer'/'register-backup-task.ps1').read_text()
    assert '-Daily' in script and "-At '18:00'" in script
    assert '-StartWhenAvailable' in script and '-LogonType Interactive' in script
    assert '-AtLogOn' in script
    assert "'unregister'" in script and '--backup-only' in script
