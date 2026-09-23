import pytest
from orcaprime.storage import Store
from orcaprime.maintenance import daily_backup


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
