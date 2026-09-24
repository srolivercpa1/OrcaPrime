import pytest
from orcaprime.order_templates import append_checklist
from orcaprime.storage import Store
from orcaprime.workshop import Workshop

def test_template_preserves_existing_notes():
    result=append_checklist('Tela trincada na entrada.','celular')
    assert result.startswith('Tela trincada na entrada.')
    assert 'Carregamento' in result
    assert append_checklist(result,'celular')==result
    with pytest.raises(ValueError):append_checklist('existente','inexistente')

def test_priority_validated_without_erasing_legacy_data(tmp_path):
    store=Store(tmp_path/'db');cid=store.save_customer({'name':'José'})
    w=Workshop(store);oid=w.save_order({'customer_id':cid,'equipment':'Notebook','priority':'URGENTE'})
    w.save_order({'diagnosis':'Novo diagnóstico'},oid)
    assert w.get_order(oid)['priority']=='URGENTE'
    with pytest.raises(ValueError):w.save_order({'priority':'INVÁLIDA'},oid)
    w.transition(oid,'CANCELADA','Cliente desistiu')
    with pytest.raises(ValueError):w.save_order({'priority':'BAIXA'},oid)
