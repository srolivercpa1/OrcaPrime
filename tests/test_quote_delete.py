import pytest
from orcaprime.storage import Store
from orcaprime.workshop import Workshop
from test_business import create_quote

@pytest.mark.parametrize('delivered',[False,True])
def test_delete_only_selected_quote_preserves_client_os_and_numbering(tmp_path,delivered):
    s=Store(tmp_path/'db');qid=create_quote(s);q=s.get_quote(qid);cid=q['customer_id']
    w=Workshop(s);oid=w.save_order({'customer_id':cid,'equipment':'Celular'})
    keep=s.save_quote(q,source_id=qid)
    if delivered:s.set_service_status([qid],'ENTREGUE')
    s.delete_quote(qid)
    assert [x['id'] for x in s.list_quotes()]==[keep]
    assert s.list_customers() and w.get_order(oid)
    with pytest.raises(ValueError,match='não encontrado'):s.get_quote(qid)
    with pytest.raises(ValueError):s.save_quote(q,qid)
    with pytest.raises(ValueError):s.delete_quote(qid)
    new=s.save_quote(q);assert new>keep
    s.backup(tmp_path/'backup.db');s.restore(tmp_path/'backup.db')
    assert qid not in [x['id'] for x in s.list_quotes()]
