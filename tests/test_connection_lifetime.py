"""Real SQLite handles must close without depending on garbage collection (Windows)."""
import sqlite3
import pytest
from orcaprime.storage import Store
from orcaprime.workshop import Workshop
from orcaprime.maintenance import _valid, daily_backup


def test_backup_restore_and_workshop_close_all_connections(tmp_path,monkeypatch):
    original=sqlite3.connect;connections=[]
    def track(*args,**kwargs):
        db=original(*args,**kwargs);connections.append(db);return db
    monkeypatch.setattr(sqlite3,'connect',track)
    store=Store(tmp_path/'original.db');cid=store.save_customer({'name':'Cliente'})
    workshop=Workshop(store);workshop.save_order({'customer_id':cid,'equipment':'Celular'})
    workshop.list_orders()
    backup=tmp_path/'backup.db';store.backup(backup)
    assert _valid(backup)
    daily_backup(store)
    restored=Store(tmp_path/'restored.db');restored.restore(backup)
    assert restored.list_customers()[0]['name']=='Cliente'
    for db in connections:
        with pytest.raises(sqlite3.ProgrammingError):db.execute('SELECT 1')
