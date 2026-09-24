import sqlite3
import pytest
from orcaprime.storage import Store
from orcaprime.users import Users
from orcaprime.workshop import Workshop


def test_backup_restores_orders_stock_payments_users_and_attachments(tmp_path):
    store=Store(tmp_path/'original.db');customer=store.save_customer({'name':'Cliente'})
    users=Users(store);actor=users.bootstrap('admin','SenhaSegura123')
    workshop=Workshop(store,actor)
    oid=workshop.save_order({'customer_id':customer,'equipment':'Notebook','warranty_days':30,'priority':'URGENTE','complaint':'Primeira linha\nSegunda linha','internal_notes':'Observação reservada'})
    workshop.add_item(oid,{'description':'Reparo','kind':'SERVICO','price':'120.00','quantity':'1'})
    for status in ('DIAGNOSTICO','AGUARDANDO_APROVACAO','EM_REPARO'):workshop.transition(oid,status,'Cliente aprovou presencialmente')
    workshop.record_payment(oid,{'amount':'50','method':'PIX'})
    attachment=tmp_path/'foto.jpg';attachment.write_bytes(b'foto de teste')
    aid=workshop.add_attachment(oid,attachment)
    backup=tmp_path/'backup.db';store.backup(backup)
    restored=Store(tmp_path/'restored.db');restored.restore(backup)
    restored_actor=Users(restored).authenticate('admin','SenhaSegura123')
    recovered=Workshop(restored,restored_actor)
    assert recovered.get_order(oid)['balance_cents']==7000
    assert recovered.get_order(oid)['priority']=='URGENTE'
    assert recovered.get_order(oid)['complaint']=='Primeira linha\nSegunda linha'
    assert recovered.get_order(oid)['internal_notes']=='Observação reservada'
    assert recovered.attachment_bytes(aid)==('foto.jpg',b'foto de teste')


def test_corrupt_workshop_backup_preserves_destination(tmp_path):
    source=Store(tmp_path/'source.db');cid=source.save_customer({'name':'Origem'});w=Workshop(source)
    oid=w.save_order({'customer_id':cid,'equipment':'Notebook'})
    with source.connect() as db:db.execute("UPDATE ws_orders SET status='INVALIDO' WHERE id=?",(oid,))
    destination=Store(tmp_path/'destination.db');destination.save_customer({'name':'Preservado'})
    with pytest.raises(ValueError):destination.restore(source.path)
    assert destination.list_customers()[0]['name']=='Preservado'


def test_pre_upgrade_backup_without_internal_notes_restores(tmp_path):
    source=Store(tmp_path/'old.db');cid=source.save_customer({'name':'Cliente antigo'})
    w=Workshop(source);oid=w.save_order({'customer_id':cid,'equipment':'Notebook'})
    with source.connect() as db:
        db.execute("UPDATE ws_orders SET data=json_remove(data,'$.internal_notes') WHERE id=?",(oid,))
    destination=Store(tmp_path/'new.db');destination.restore(source.path)
    recovered=Workshop(destination).get_order(oid)
    assert recovered['equipment']=='Notebook'
