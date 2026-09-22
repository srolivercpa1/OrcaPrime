from decimal import Decimal
import pytest
from orcaprime.domain import calculate, money, number
from orcaprime.storage import Store
from orcaprime.pdf import export_quote


def test_fractional_rounding_and_discount():
    assert calculate([{'quantity':'2,5','price':'10,00'}], '3,00') == (2500,300,2200)
    assert calculate([{'quantity':'3','price':'0,335'}], '0') == (102,0,102)

@pytest.mark.parametrize('value', ['NaN','Infinity','-1','abc','1e20'])
def test_invalid_money(value):
    with pytest.raises(ValueError): money(value)

@pytest.mark.parametrize('qty', ['0','-1','NaN','1000000000000'])
def test_invalid_quantity(qty):
    with pytest.raises(ValueError): calculate([{'quantity':qty,'price':'1'}], 0)


def test_discount_cannot_exceed_subtotal():
    with pytest.raises(ValueError): calculate([{'quantity':'1','price':'10'}], '11')

@pytest.fixture
def store(tmp_path): return Store(tmp_path/'business.db')

def create_quote(s):
    cid=s.save_customer({'name':'João & Filhos','phone':'64993265529'})
    return s.save_quote({'customer_id':cid,'valid_until':'2026-12-31','discount':'3','notes':'Garantia <combinada>', 'items':[{'description':'Suporte técnico','quantity':'2,5','price':'10','unit':'h'}]})

def test_crud_snapshot_and_search(store):
    qid=create_quote(store)
    q=store.get_quote(qid)
    assert q['total_cents']==2200
    store.save_customer({'name':'Novo nome'},q['customer_id'])
    assert store.get_quote(qid)['customer']['name']=='João & Filhos'
    assert len(store.list_quotes('João'))==1
    assert store.list_quotes('inexistente')==[]
    store.set_status(qid,'APROVADO')
    assert store.get_quote(qid)['status']=='APROVADO'
    with pytest.raises(ValueError): store.set_status(qid,'injetar')

def test_catalog_and_settings(store):
    iid=store.save_item({'description':'Manutenção','price':'49,99','unit':'un','kind':'SERVIÇO'})
    assert store.list_items()[0]['price_cents']==4999
    store.save_item({'description':'Visita','price':'70','unit':'un','kind':'SERVIÇO'},iid)
    assert store.list_items()[0]['description']=='Visita'
    store.save_company({'name':'OLIVERTECH SOLUÇÕES','phone':'64993265529'})
    assert store.company()['name']=='OLIVERTECH SOLUÇÕES'

def test_backup_and_reject_invalid_restore(store,tmp_path):
    create_quote(store)
    backup=tmp_path/'backup.db'; store.backup(backup)
    invalid=tmp_path/'invalid.db'; invalid.write_text('no database')
    with pytest.raises(ValueError): store.restore(invalid)
    assert len(store.list_quotes())==1
    create_quote(store); assert len(store.list_quotes())==2
    store.restore(backup); assert len(store.list_quotes())==1

def test_pdf_handles_long_content(store,tmp_path):
    qid=create_quote(store); q=store.get_quote(qid)
    q['items']*=85
    out=tmp_path/'quote.pdf'; export_quote(out,q,{'name':'OrçaPrime','address':'Rua A & B'})
    assert out.read_bytes().startswith(b'%PDF-')
    assert out.stat().st_size>3000

def test_edit_preserves_number(store):
    qid=create_quote(store); q=store.get_quote(qid)
    q['discount']='0'; q['items'][0]['price']='20'
    store.save_quote(q,qid)
    assert store.get_quote(qid)['number']==q['number']
    assert store.get_quote(qid)['total_cents']==5000

def test_malformed_backup_never_replaces_live_data(store,tmp_path):
    import sqlite3,json
    create_quote(store)
    broken=tmp_path/'broken.db';Store(broken)
    with sqlite3.connect(broken) as db: db.execute("INSERT INTO quotes(data) VALUES('{}')")
    with pytest.raises(ValueError):store.restore(broken)
    assert len(store.list_customers())==1
    assert store.list_quotes()[0]['customer']['name']=='João & Filhos'

def test_duplicate_preserves_historical_customer(store):
    qid=create_quote(store);q=store.get_quote(qid)
    store.save_customer({'name':'Nome novo'},q['customer_id'])
    copy_id=store.save_quote(q,source_id=qid)
    assert store.get_quote(copy_id)['customer']['name']=='João & Filhos'
    assert store.get_quote(copy_id)['number']!=q['number']
