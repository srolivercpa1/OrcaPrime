import pytest
from PIL import Image
from pypdf import PdfReader
from orcaprime.storage import Store
from orcaprime.workshop import Workshop, validate_workshop_database
from orcaprime.document_actions import DocumentActions


def test_customer_removal_deletes_orders_but_keeps_cash_and_stock(tmp_path):
    s=Store(tmp_path/'db');w=Workshop(s);cid=s.save_customer({'name':'Excluir'});other=s.save_customer({'name':'Manter'})
    oid=w.save_order({'customer_id':cid,'equipment':'Celular'});keep=w.save_order({'customer_id':other,'equipment':'Tablet'})
    part=w.save_part({'description':'Tela','price':'20'});w.stock_move(part,'2','ENTRADA','Compra')
    w.add_item(oid,{'description':'Tela','kind':'PECA','part_id':part,'quantity':'1','price':'20'})
    for status in ('DIAGNOSTICO','AGUARDANDO_APROVACAO','EM_REPARO'):w.transition(oid,status,'Aprovado')
    w.record_payment(oid,{'amount':'20','method':'PIX'})
    photo=tmp_path/'photo.png';Image.new('RGB',(20,20),'blue').save(photo);w.add_attachment(oid,photo)
    for status in ('EM_TESTES','PRONTA'):w.transition(oid,status)
    w.save_order({'receiver':'Cliente','final_checklist':'Testado'},oid);w.transition(oid,'ENTREGUE')
    returned=w.create_return(oid,'Garantia')
    s.delete_customer(cid)
    assert [o['id'] for o in w.list_orders()]==[keep]
    assert w.list_parts()[0]['quantity']=='1'
    with s.connect() as db:
        assert db.execute('SELECT SUM(amount_cents) FROM ws_cash').fetchone()[0]==2000
        for table in ('ws_items','ws_events','ws_attachments','ws_payments'):
            assert not db.execute(f'SELECT 1 FROM {table} WHERE order_id IN (?,?)',(oid,returned)).fetchone()
        validate_workshop_database(db)
    s.backup(tmp_path/'copy.db');s.restore(tmp_path/'copy.db')
    assert [o['id'] for o in w.list_orders()]==[keep]


def test_logo_persists_after_source_removed_and_in_backup_and_documents(tmp_path):
    s=Store(tmp_path/'db');w=Workshop(s);cid=s.save_customer({'name':'Cliente'});oid=w.save_order({'customer_id':cid,'equipment':'Celular'})
    source=tmp_path/'logo.png';Image.new('RGBA',(400,100),(0,80,180,255)).save(source)
    s.save_company_logo(source);source.unlink()
    s.save_company({'name':'Loja'});s.backup(tmp_path/'backup.db');s.restore(tmp_path/'backup.db')
    actions=DocumentActions(w,s.company())
    for kind in ('OS','GARANTIA'):
        for paper in ('A4','58mm','80mm'):
            path=tmp_path/f'{kind}-{paper}.pdf';actions.generate(oid,path,kind,paper)
            reader=PdfReader(path);assert len(reader.pages[0].images)==1
            assert 'Cliente' in ''.join(p.extract_text() for p in reader.pages)
    s.save_company_logo(None)
    path=tmp_path/'removed.pdf';actions.generate(oid,path,'OS','A4')
    assert len(PdfReader(path).pages[0].images)==0


def test_invalid_logo_keeps_previous(tmp_path):
    s=Store(tmp_path/'db');source=tmp_path/'logo.png';Image.new('RGB',(10,10),'blue').save(source);s.save_company_logo(source)
    old=s.company_logo();source.write_text('invalid')
    with pytest.raises(ValueError):s.save_company_logo(source)
    assert s.company_logo()==old


def test_delete_customer_rechecks_confirmation_and_is_atomic(tmp_path):
    s=Store(tmp_path/'db');w=Workshop(s);cid=s.save_customer({'name':'Cliente'})
    expected=s.customer_order_ids(cid);oid=w.save_order({'customer_id':cid,'equipment':'Notebook'})
    with pytest.raises(ValueError,match='mudaram'):s.delete_customer(cid,expected_orders=expected)
    assert s.list_customers() and w.get_order(oid)
    with s.connect() as db:
        db.execute("CREATE TRIGGER reject_order_delete BEFORE DELETE ON ws_orders BEGIN SELECT RAISE(ABORT,'stop'); END")
    import sqlite3
    with pytest.raises(sqlite3.IntegrityError):s.delete_customer(cid)
    assert s.list_customers() and w.get_order(oid)['events']


def test_corrupt_logo_is_rejected_by_backup_validation(tmp_path):
    from orcaprime.backup_validation import validate_database
    s=Store(tmp_path/'db')
    with s.connect() as db:
        db.execute("INSERT INTO meta VALUES('company_logo','invalid')")
        with pytest.raises(ValueError):validate_database(db)
