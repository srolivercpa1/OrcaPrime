import pytest
from orcaprime.storage import Store
from test_business import create_quote
from orcaprime.workshop import Workshop

def test_delete_customer_preserves_existing_orders_quotes_and_backup(tmp_path):
    s=Store(tmp_path/'db');qid=create_quote(s);cid=s.get_quote(qid)['customer_id']
    ws=Workshop(s);oid=ws.save_order({'customer_id':cid,'equipment':'Celular'})
    s.delete_customer(cid)
    assert s.list_customers()==[]
    assert s.get_quote(qid)['customer']['name']
    assert ws.get_order(oid)['customer']['name']
    ws.save_order({'customer_id':cid,'equipment':'Celular revisado'},oid)
    s.save_quote(s.get_quote(qid),qid)
    with pytest.raises(ValueError):ws.save_order({'customer_id':cid,'equipment':'Novo'})
    with pytest.raises(ValueError):s.save_customer({'name':'Reativado'},cid)
    s.backup(tmp_path/'copy.db');s.restore(tmp_path/'copy.db')
    assert s.list_customers()==[] and ws.get_order(oid)['equipment']=='Celular revisado'


def test_delivery_moves_quote_and_preserves_report_and_history(tmp_path):
    s=Store(tmp_path/'db');qid=create_quote(s)
    s.set_service_status([qid],'EM_ANDAMENTO','Diagnóstico iniciado','Ana')
    s.set_service_status([qid],'PRONTO','Testado','Ana')
    s.set_service_status([qid],'ENTREGUE','Retirado por João','Ana')
    q=s.get_quote(qid)
    assert s.list_quotes(delivered=False)==[]
    assert s.list_quotes(delivered=True)[0]['id']==qid
    assert q['delivered_at'] and q['service_history'][-1]['note']=='Retirado por João'
    assert q['items'][0]['description']=='Suporte técnico'
    assert q['status']=='RASCUNHO'
    with pytest.raises(ValueError,match='entregue'):s.save_quote(dict(q,discount='3'),qid)
    duplicate=s.save_quote(dict(q,discount='3'),source_id=qid)
    assert s.get_quote(duplicate)['service_status']=='AGUARDANDO'
    assert not s.get_quote(duplicate)['service_history']
    s.backup(tmp_path/'backup.db');s.restore(tmp_path/'backup.db')
    assert s.get_quote(qid)['service_history']==q['service_history']

def test_batch_status_is_atomic_for_invalid_record(tmp_path):
    s=Store(tmp_path/'db');qid=create_quote(s)
    with pytest.raises(ValueError):s.set_service_status([qid,999],'ENTREGUE')
    assert s.get_quote(qid).get('service_status','AGUARDANDO')=='AGUARDANDO'


def test_full_pdf_contains_device_service_and_delivery(tmp_path):
    from orcaprime.pdf import export_quote
    from pypdf import PdfReader
    s=Store(tmp_path/'db');qid=create_quote(s);q=s.get_quote(qid)
    s.save_quote(dict(q,equipment='Notebook',serial='XYZ123',service_report='Placa reparada e testada'),qid)
    s.set_service_status([qid],'ENTREGUE','Retirado por Joao','Ana')
    path=tmp_path/'report.pdf';export_quote(path,s.get_quote(qid),s.company(),report=True)
    text='\n'.join(page.extract_text() for page in PdfReader(path).pages)
    for expected in ('Notebook','XYZ123','Placa reparada e testada','Retirado por Joao','Ana','Suporte técnico'):
        assert expected in text

@pytest.mark.parametrize('field,value',[('service_status','INVALID'),('service_history',{}),('delivered_at','bad')])
def test_invalid_workflow_backup_is_rejected(tmp_path,field,value):
    import json
    from orcaprime.backup_validation import validate_database
    s=Store(tmp_path/'db');qid=create_quote(s)
    with s.connect() as db:
        q=s.get_quote(qid);q[field]=value
        db.execute('UPDATE quotes SET data=? WHERE id=?',(json.dumps(q),qid))
    with s.connect() as db,pytest.raises(ValueError):validate_database(db)

def test_deleted_customer_delivered_os_and_warranty_are_preserved(tmp_path):
    s=Store(tmp_path/'db');cid=s.save_customer({'name':'Cliente da garantia'});w=Workshop(s)
    oid=w.save_order({'customer_id':cid,'equipment':'Notebook'})
    w.add_item(oid,{'description':'Serviço','kind':'SERVICO','quantity':'1','price':'0'})
    for status in ('DIAGNOSTICO','AGUARDANDO_APROVACAO','EM_REPARO','EM_TESTES','PRONTA'):
        w.transition(oid,status,'Aprovado pelo cliente')
    w.save_order({'receiver':'Cliente','final_checklist':'Testado'},oid);w.transition(oid,'ENTREGUE')
    before=w.get_order(oid);s.delete_customer(cid)
    assert w.get_order(oid)==before and not s.list_customers()
    returned=w.create_return(oid,'Mesmo defeito')
    assert w.get_order(returned)['customer']['name']=='Cliente da garantia'
