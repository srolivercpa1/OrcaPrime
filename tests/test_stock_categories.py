import pytest
from orcaprime.storage import Store
from orcaprime.workshop import Workshop

@pytest.mark.parametrize('description,expected',[
    ('Bateria iPhone 11','Bateria'),('  BATERIA Samsung A20','Bateria'),
    ('Baterias Motorola','Bateria'),('Tela iPhone 13','Tela'),('Telas Samsung','Tela'),
    ('Conector de carga','Conector'),('Cabo USB-C','Cabo'),('Câmera traseira','Câmera'),
    ('camera frontal','Câmera'),('Película 3D','Película'),('Flex volume','Flex'),
    ('Alto-falante iPhone','Alto-falante'),('Tela-A20','Tela'),('12345','Outros')])
def test_category_from_product_prefix(description,expected):
    from orcaprime.stock_categories import category_for
    assert category_for(description)==expected


def test_existing_parts_and_renames_change_category_without_stock_changes(tmp_path):
    s=Store(tmp_path/'db');w=Workshop(s)
    pid=w.save_part({'description':'Bateria iPhone','price':'50','cost':'20','sku':'BAT1'})
    w.stock_move(pid,'4','ENTRADA','Compra')
    assert w.list_parts()[0]['category']=='Bateria'
    w.save_part({'description':'Tela iPhone','price':'50','cost':'20','sku':'BAT1'},pid)
    p=w.list_parts()[0]
    assert p['category']=='Tela' and p['quantity']=='4' and p['price_cents']==5000
    s.backup(tmp_path/'backup.db');s.restore(tmp_path/'backup.db')
    assert w.list_parts()[0]['category']=='Tela' and len(w.list_movements())==1
