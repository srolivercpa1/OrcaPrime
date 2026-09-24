import pytest
from pypdf import PdfReader
from orcaprime.storage import Store
from orcaprime.workshop import Workshop
from orcaprime.document_actions import DocumentActions
from orcaprime.service_documents import export_service_document

@pytest.fixture
def state(tmp_path):
    store=Store(tmp_path/'data.db');cid=store.save_customer({'name':'José'})
    w=Workshop(store);oid=w.save_order({'customer_id':cid,'equipment':'Celular','internal_notes':'SEGREDO_INTERNO_123'})
    return w,oid,DocumentActions(w,{'name':'Oficina'})

def test_cancel_and_print_failure_do_not_mutate_orders(state,tmp_path,monkeypatch):
    w,oid,actions=state;before=w.get_order(oid)
    assert actions.generate(oid,None,'OS','A4') is None
    path=actions.generate(oid,tmp_path/'os.pdf','OS','A4')
    with pytest.raises(ValueError):actions.send(path,'')
    def failed(*args):raise OSError('Fila indisponível')
    monkeypatch.setattr('orcaprime.service_documents.print_document',failed)
    with pytest.raises(OSError):actions.send(path,'Impressora')
    assert w.get_order(oid)==before
    text=''.join(p.extract_text() for p in PdfReader(path).pages)
    assert 'SEGREDO_INTERNO_123' not in text
    assert w.get_order(oid)['internal_notes']=='SEGREDO_INTERNO_123'

def test_delivery_requires_delivered_and_preserves_details(state,tmp_path):
    w,oid,actions=state
    with pytest.raises(ValueError):actions.generate(oid,tmp_path/'early.pdf','ENTREGA','A4')
    for status in ('DIAGNOSTICO','AGUARDANDO_APROVACAO','EM_REPARO','EM_TESTES','PRONTA'):
        w.transition(oid,status,'Aprovado presencialmente')
    w.save_order({'receiver':'Maria da Silva','final_checklist':'Tela e áudio testados'},oid)
    w.transition(oid,'ENTREGUE')
    for paper in ('A4','58mm','80mm'):
        p=actions.generate(oid,tmp_path/(paper+'.pdf'),'ENTREGA',paper)
        text=' '.join(''.join(p.extract_text() for p in PdfReader(p).pages).split())
        assert 'Maria da Silva' in text and 'Tela e áudio testados' in text
        assert 'SEGREDO_INTERNO_123' not in text
    with pytest.raises(ValueError):actions.generate(oid,tmp_path/'invalid.pdf','OS','ETIQUETA')
