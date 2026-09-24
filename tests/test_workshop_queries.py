from datetime import date
import pytest
from orcaprime.storage import Store
from orcaprime.workshop import Workshop
from orcaprime.workshop_queries import OrderFilters, filter_orders, summarize_orders, equipment_history, productivity

TODAY = date(2026, 9, 24)

def test_overdue_excludes_closed_and_invalid_dates():
    rows = [dict(id=i, status=s, due_date=d) for i,s,d in [
        (1,'RECEBIDA','2026-09-23'),(2,'ENTREGUE','2026-09-23'),
        (3,'CANCELADA','2026-09-23'),(4,'RECEBIDA',''),
        (5,'RECEBIDA','data antiga'),(6,'RECEBIDA','2026-09-24')]]
    assert [r['id'] for r in filter_orders(rows,OrderFilters(deadline='overdue'),TODAY)] == [1]
    summary=summarize_orders(rows,TODAY)
    assert (summary['active'],summary['overdue'],summary['invalid_dates']) == (4,1,1)
    assert [r['id'] for r in summary['due_today']] == [6]

def test_combined_filters_and_default_priority():
    rows=[dict(id=1,number='OS-01',customer={'name':'José'},technician=' Ana ',status='RECEBIDA'),
          dict(id=2,number='OS-02',customer={'name':'José'},technician='Bia',priority='URGENTE',status='RECEBIDA')]
    f=OrderFilters(text='josé',technician='ana',priority='NORMAL',deadline='undated')
    assert [o['id'] for o in filter_orders(rows,f,TODAY)] == [1]
    assert filter_orders(rows,OrderFilters(text='não existe'),TODAY)==[]
    assert 'priority' not in rows[0]

def test_blank_serial_is_customer_history():
    rows=[{'id':1,'customer_id':7,'serial':'','model':'A'}, {'id':2,'customer_id':8,'serial':'','model':'A'}, {'id':3,'customer_id':7,'serial':'123'}]
    result=equipment_history(rows,7,'')
    assert result['scope']=='customer'
    assert [o['id'] for o in result['orders']]==[1,3]
    assert [o['id'] for o in equipment_history(rows,7,'123')['orders']]==[3]

@pytest.fixture
def workshop(tmp_path):
    store=Store(tmp_path/'data.db'); cid=store.save_customer({'name':'Cliente'})
    w=Workshop(store); w.save_order({'customer_id':cid,'equipment':'Notebook'})
    return w

def test_dashboard_does_not_leak_finance_and_rechecks_user(workshop):
    store=workshop.store
    with store.connect() as db:
        db.execute('CREATE TABLE app_users(id INTEGER PRIMARY KEY,name TEXT,role TEXT,active INTEGER)')
        db.execute("INSERT INTO app_users VALUES(9,'Atendente','ATENDIMENTO',1)")
    w=Workshop(store,{'id':9,'name':'Admin falso','role':'ADMIN'})
    result=w.dashboard(TODAY)
    assert result['active']==1
    assert 'finance' not in result and 'low_stock' not in result
    with store.connect() as db: db.execute('UPDATE app_users SET active=0 WHERE id=9')
    with pytest.raises(PermissionError):w.dashboard(TODAY)
    with pytest.raises(PermissionError):w.query_orders(OrderFilters(),TODAY)

def test_productivity_counts_once_and_includes_boundaries():
    event=lambda d:dict(action='SITUACAO',target='ENTREGUE',created_at=d+'T12:00:00')
    rows=[dict(id=1,technician='Ana',events=[event('2026-09-01'),event('2026-09-24')]),
          dict(id=2,technician='Ana',events=[event('2026-09-24')]),
          dict(id=3,technician='Bia',events=[event('2026-08-31')])]
    assert productivity(rows,date(2026,9,1),TODAY)==[{'technician':'Ana','delivered_count':2,'delivered_order_ids':[1,2]}]
    with pytest.raises(ValueError):productivity(rows,TODAY,date(2026,9,1))

def test_productivity_service_rejects_technician(workshop):
    w=Workshop(workshop.store,{'role':'TECNICO','name':'T','id':0})
    with pytest.raises(PermissionError):w.productivity(date(2026,9,1),TODAY)

def test_no_delivery_date_is_not_invented():
    rows=[dict(id=1,technician='Ana',status='ENTREGUE',delivered_at='2026-09-10',events=[])]
    assert productivity(rows,date(2026,9,1),TODAY)==[]

def test_active_filter_excludes_closed_orders():
    rows=[{'id':1,'status':'RECEBIDA'},{'id':2,'status':'ENTREGUE'},{'id':3,'status':'CANCELADA'}]
    assert [o['id'] for o in filter_orders(rows,OrderFilters(active_only=True),TODAY)]==[1]

def test_invalid_date_suffix_is_not_valid_deadline(workshop):
    from orcaprime.workshop_queries import parsed_date
    assert parsed_date('2020-01-01-invalida') is None
    assert summarize_orders([{'status':'RECEBIDA','due_date':'2020-01-01-invalida'}],TODAY)['overdue']==0
    with workshop.store.connect() as db:
        db.execute("UPDATE ws_orders SET data=json_set(data,'$.due_date','0000-invalida')")
    assert workshop.report()['overdue']==[]
