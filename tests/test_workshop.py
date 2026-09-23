import tempfile
import unittest
from pathlib import Path
from orcaprime.storage import Store
from orcaprime.workshop import Workshop, validate_workshop_database

class WorkshopTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.store=Store(Path(self.tmp.name)/'db.sqlite')
        self.cid=self.store.save_customer({'name':'Cliente'})
        self.w=Workshop(self.store)
        self.oid=self.w.save_order({'customer_id':self.cid,'equipment':'Notebook','complaint':'Não liga'})
    def tearDown(self): self.tmp.cleanup()
    def test_flow_stock_idempotency_payment_and_return(self):
        p=self.w.save_part({'description':'Fonte','price':'80','cost':'30'})
        self.w.stock_move(p,'2','ENTRADA','Compra')
        item={'description':'Fonte','kind':'PECA','part_id':p,'quantity':'1','price':'80','cost':'30','request_id':'item1'}
        self.assertEqual(self.w.add_item(self.oid,item),self.w.add_item(self.oid,item))
        self.assertEqual(self.w.list_parts()[0]['quantity'],'1')
        self.w.transition(self.oid,'DIAGNOSTICO'); self.w.transition(self.oid,'AGUARDANDO_APROVACAO')
        self.w.transition(self.oid,'EM_REPARO','Cliente aprovou por telefone')
        with self.assertRaises(ValueError): self.w.remove_item(self.oid,1)
        pay={'amount':'80','method':'PIX','request_id':'pay1'}
        self.assertEqual(self.w.record_payment(self.oid,pay),self.w.record_payment(self.oid,pay))
        self.w.transition(self.oid,'EM_TESTES'); self.w.transition(self.oid,'PRONTA')
        self.w.save_order({'receiver':'Cliente','final_checklist':'Liga normalmente'},self.oid)
        self.w.transition(self.oid,'ENTREGUE')
        ret=self.w.create_return(self.oid,'Mesmo defeito')
        self.assertEqual(self.w.get_order(ret)['parent_id'],self.oid)
        with self.store.connect() as db: validate_workshop_database(db)
    def test_rollback_permissions_and_overpayment(self):
        p=self.w.save_part({'description':'Peça'})
        with self.assertRaises(ValueError): self.w.add_item(self.oid,{'description':'Peça','part_id':p,'quantity':'1','price':'10','kind':'PECA'})
        self.assertEqual(self.w.get_order(self.oid)['items'],[])
        with self.assertRaises(PermissionError): Workshop(self.store,{'id':2,'name':'T','role':'TECNICO'}).record_payment(self.oid,{'amount':'1'})
        with self.assertRaises(ValueError): self.w.record_payment(self.oid,{'amount':'1'})
    def test_reverse_and_attachments(self):
        self.w.add_item(self.oid,{'description':'Serviço','kind':'SERVICO','quantity':'1.25','price':'10.02'})
        self.w.transition(self.oid,'DIAGNOSTICO'); self.w.transition(self.oid,'AGUARDANDO_APROVACAO'); self.w.transition(self.oid,'EM_REPARO','Aprovado')
        p=self.w.record_payment(self.oid,{'amount':'5','method':'Dinheiro'})
        self.w.reverse_payment(p,'Erro'); self.assertEqual(self.w.get_order(self.oid)['paid_cents'],0)
        f=Path(self.tmp.name)/'foto.txt'; f.write_bytes(b'photo')
        aid=self.w.add_attachment(self.oid,f); f.unlink()
        self.assertEqual(self.w.attachment_bytes(aid),('foto.txt',b'photo'))
    def test_cancel_returns_stock_once_and_freezes_order(self):
        p=self.w.save_part({'description':'Peça'})
        self.w.stock_move(p,'1.25','ENTRADA','Compra')
        self.w.add_item(self.oid,{'description':'Peça','kind':'PECA','part_id':p,'quantity':'1.25','price':'10'})
        self.w.transition(self.oid,'CANCELADA','Recusado'); self.w.transition(self.oid,'CANCELADA','Recusado')
        self.assertEqual(self.w.list_parts()[0]['quantity'],'1.25')
        with self.assertRaises(ValueError):self.w.save_order({'notes':'alterar'},self.oid)
    def test_validator_rejects_corrupt_customer_and_item(self):
        with self.store.connect() as db:
            db.execute("UPDATE ws_orders SET data=json_set(data,'$.customer.id',999) WHERE id=?",(self.oid,))
        with self.store.connect() as db:
            with self.assertRaises(ValueError):validate_workshop_database(db)
    def test_finance_title_settlement_is_not_duplicated(self):
        a=self.w.save_account({'description':'Fornecedor','kind':'PAGAR','amount':'20','due_date':'2026-10-01'})
        self.w.settle_account(a,'PIX')
        with self.assertRaises(ValueError):self.w.settle_account(a,'PIX')
        self.assertEqual(sum(x['amount_cents'] for x in self.w.list_cash()),-2000)
        with self.store.connect() as db:validate_workshop_database(db)
    def test_database_role_overrides_forged_actor(self):
        with self.store.connect() as db:
            db.execute('CREATE TABLE app_users(id INTEGER PRIMARY KEY,name TEXT,role TEXT,active INTEGER)')
            db.execute("INSERT INTO app_users VALUES(9,'Técnico','TECNICO',1)")
        forged=Workshop(self.store,{'id':9,'name':'Admin','role':'ADMIN'})
        with self.assertRaises(PermissionError):forged.save_part({'description':'Negado'})
    def test_validator_rejects_missing_part_shape(self):
        p=self.w.save_part({'description':'Peça'})
        with self.store.connect() as db:db.execute("UPDATE ws_parts SET data='{}' WHERE id=?",(p,))
        with self.store.connect() as db:
            with self.assertRaises(ValueError):validate_workshop_database(db)
    def test_report_cost_and_margin_use_decimal_rounding(self):
        self.w.add_item(self.oid,{'description':'Serviço','quantity':'1.25','price':'10.02','cost':'2.01'})
        result=self.w.report()['order_results'][0]
        self.assertEqual((result['total_cents'],result['cost_cents'],result['margin_cents']),(1253,251,1002))
    def test_approval_and_delivery_require_explicit_evidence(self):
        self.w.transition(self.oid,'DIAGNOSTICO');self.w.transition(self.oid,'AGUARDANDO_APROVACAO')
        with self.assertRaises(ValueError):self.w.transition(self.oid,'EM_REPARO')
        self.w.transition(self.oid,'EM_REPARO','Maria aprovou presencialmente')
        self.w.transition(self.oid,'EM_TESTES');self.w.transition(self.oid,'PRONTA')
        with self.assertRaises(ValueError):self.w.transition(self.oid,'ENTREGUE')
        self.assertEqual(self.w.get_order(self.oid)['status'],'PRONTA')
    def test_disabled_actor_cannot_read(self):
        with self.store.connect() as db:
            db.execute('CREATE TABLE app_users(id INTEGER PRIMARY KEY,name TEXT,role TEXT,active INTEGER)')
            db.execute("INSERT INTO app_users VALUES(9,'Admin','ADMIN',0)")
        w=Workshop(self.store,{'id':9,'name':'Admin','role':'ADMIN'})
        with self.assertRaises(PermissionError):w.list_orders()
