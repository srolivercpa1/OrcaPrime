"""Transactional, offline service-order rules. Money is integer cents, stock milliunits."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from .finance_extras import FinanceExtras

STATUSES = ('RECEBIDA','DIAGNOSTICO','AGUARDANDO_APROVACAO','AGUARDANDO_PECA','EM_REPARO','EM_TESTES','PRONTA','ENTREGUE','CANCELADA')
FIELDS = ('equipment','brand','model','serial','accessories','complaint','diagnosis','technician','priority','due_date','checklist','notes','approval_note','warranty_terms','receiver','final_checklist')
TABLES = ('ws_orders','ws_items','ws_events','ws_parts','ws_movements','ws_payments','ws_suppliers','ws_accounts','ws_cash','ws_attachments')

def scaled(value, scale=100):
    try:
        n=Decimal(str(value).replace(',','.'))
        if not n.is_finite() or abs(n)>Decimal('1000000000'): raise ValueError()
        return int((n*scale).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
    except (InvalidOperation,ValueError,TypeError): raise ValueError('Valor numérico inválido.') from None

def qty(value):
    n=scaled(value,1000)
    if Decimal(str(value).replace(',','.'))*1000 != n: raise ValueError('Quantidade permite até três casas decimais.')
    return n

def quantity(n): return format(Decimal(n)/1000,'f').rstrip('0').rstrip('.') if n%1000 else str(n//1000)
def now(): return datetime.now().isoformat(timespec='seconds')
def raw(data): return json.dumps(data,ensure_ascii=False)

class Workshop(FinanceExtras):
    def __init__(self,store,actor=None):
        self.store=store; self.actor=actor or {'id':0,'name':'Local','role':'ADMIN'}
        with sqlite3.connect(self.store.path) as existing:
            marker=existing.execute("SELECT value FROM meta WHERE key='workshop_schema'").fetchone()
            if marker and marker[0]!='1': raise ValueError('Versão de assistência incompatível.')
            needs_backup=not marker and any(existing.execute(f'SELECT 1 FROM {table} LIMIT 1').fetchone() for table in ('customers','catalog','quotes'))
        if needs_backup: self.store.backup(self.store.path.with_name('antes-assistencia-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.db'))
        with self.connect() as db:
            db.executescript('''
            BEGIN IMMEDIATE;
            CREATE TABLE IF NOT EXISTS ws_orders(id INTEGER PRIMARY KEY AUTOINCREMENT,customer_id INTEGER NOT NULL REFERENCES customers(id),status TEXT NOT NULL,data TEXT NOT NULL,approved_cents INTEGER, parent_id INTEGER REFERENCES ws_orders(id));
            CREATE TABLE IF NOT EXISTS ws_parts(id INTEGER PRIMARY KEY,data TEXT NOT NULL,stock INTEGER NOT NULL DEFAULT 0 CHECK(stock>=0));
            CREATE TABLE IF NOT EXISTS ws_items(id INTEGER PRIMARY KEY,order_id INTEGER NOT NULL REFERENCES ws_orders(id),data TEXT NOT NULL,part_id INTEGER REFERENCES ws_parts(id),units INTEGER NOT NULL CHECK(units>0),total_cents INTEGER NOT NULL CHECK(total_cents>=0),request_id TEXT UNIQUE);
            CREATE TABLE IF NOT EXISTS ws_events(id INTEGER PRIMARY KEY,order_id INTEGER NOT NULL REFERENCES ws_orders(id),data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS ws_movements(id INTEGER PRIMARY KEY,part_id INTEGER NOT NULL REFERENCES ws_parts(id),quantity INTEGER NOT NULL,kind TEXT NOT NULL,note TEXT NOT NULL,order_id INTEGER REFERENCES ws_orders(id),created_at TEXT NOT NULL,actor TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS ws_payments(id INTEGER PRIMARY KEY,order_id INTEGER NOT NULL REFERENCES ws_orders(id),amount_cents INTEGER NOT NULL CHECK(amount_cents>0),data TEXT NOT NULL,reversed INTEGER NOT NULL DEFAULT 0 CHECK(reversed IN (0,1)),request_id TEXT UNIQUE);
            CREATE TABLE IF NOT EXISTS ws_suppliers(id INTEGER PRIMARY KEY,data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS ws_accounts(id INTEGER PRIMARY KEY,data TEXT NOT NULL,amount_cents INTEGER NOT NULL CHECK(amount_cents>0),settled INTEGER NOT NULL DEFAULT 0 CHECK(settled IN (0,1)));
            CREATE TABLE IF NOT EXISTS ws_cash(id INTEGER PRIMARY KEY,data TEXT NOT NULL,amount_cents INTEGER NOT NULL,payment_id INTEGER REFERENCES ws_payments(id),account_id INTEGER REFERENCES ws_accounts(id));
            CREATE TABLE IF NOT EXISTS ws_attachments(id INTEGER PRIMARY KEY,order_id INTEGER NOT NULL REFERENCES ws_orders(id),filename TEXT NOT NULL,content BLOB NOT NULL,created_at TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS ws_items_order ON ws_items(order_id);
            INSERT OR IGNORE INTO meta VALUES('workshop_schema','1');
            COMMIT;
            ''')
    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.store.path,timeout=15); db.row_factory=sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            db.execute('BEGIN IMMEDIATE')
            yield db; db.commit()
        except Exception: db.rollback(); raise
        finally: db.close()
    def _allow(self,*roles):
        role=self.actor.get('role')
        with sqlite3.connect(self.store.path,timeout=15) as db:
            if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='app_users'").fetchone() and db.execute('SELECT 1 FROM app_users LIMIT 1').fetchone():
                user=db.execute('SELECT name,role,active FROM app_users WHERE id=?',(self.actor.get('id'),)).fetchone()
                if not user or not user[2]: raise PermissionError('Usuário inativo ou não autenticado.')
                role=user[1]; self.actor=dict(self.actor,name=user[0],role=role)
        if role not in ('ADMIN',)+roles: raise PermissionError('Perfil sem permissão para esta operação.')
    def _event(self,db,oid,action,**data):
        db.execute('INSERT INTO ws_events(order_id,data) VALUES(?,?)',(oid,raw(dict(data,action=action,created_at=now(),actor=dict(self.actor)))))
    def _order(self,db,oid):
        row=db.execute('SELECT * FROM ws_orders WHERE id=?',(oid,)).fetchone()
        if row is None: raise ValueError('OS não encontrada.')
        return row
    def _editable(self,row,pricing=False):
        if row['status'] in ('ENTREGUE','CANCELADA'): raise ValueError('OS encerrada não pode ser alterada.')
        if pricing and row['approved_cents'] is not None: raise ValueError('Orçamento aprovado está congelado; abra uma nova OS para alterações de preço.')
    def _total(self,db,oid): return db.execute('SELECT COALESCE(SUM(total_cents),0) FROM ws_items WHERE order_id=?',(oid,)).fetchone()[0]
    def _paid(self,db,oid): return db.execute('SELECT COALESCE(SUM(amount_cents),0) FROM ws_payments WHERE order_id=? AND reversed=0',(oid,)).fetchone()[0]
    def _get(self,db,oid):
        r=self._order(db,oid); d=dict(json.loads(r['data']),id=r['id'],customer_id=r['customer_id'],status=r['status'],parent_id=r['parent_id'],approved_cents=r['approved_cents'])
        d['items']=[dict(json.loads(x['data']),id=x['id'],part_id=x['part_id'],total_cents=x['total_cents']) for x in db.execute('SELECT * FROM ws_items WHERE order_id=? ORDER BY id',(oid,))]
        d['payments']=[dict(json.loads(x['data']),id=x['id'],amount_cents=x['amount_cents'],reversed=bool(x['reversed'])) for x in db.execute('SELECT * FROM ws_payments WHERE order_id=? ORDER BY id',(oid,))]
        d['events']=[dict(json.loads(x['data']),id=x['id']) for x in db.execute('SELECT * FROM ws_events WHERE order_id=? ORDER BY id',(oid,))]
        d['attachments']=[dict(x) for x in db.execute('SELECT id,filename,length(content) AS size,created_at FROM ws_attachments WHERE order_id=?',(oid,))]
        d['total_cents']=self._total(db,oid); d['paid_cents']=self._paid(db,oid); d['balance_cents']=d['total_cents']-d['paid_cents']
        return d
    def get_order(self,id):
        self._allow('ATENDIMENTO','TECNICO','FINANCEIRO')
        with self.connect() as db: return self._get(db,id)
    def list_orders(self,search=''):
        self._allow('ATENDIMENTO','TECNICO','FINANCEIRO')
        with self.connect() as db:
            rows=[self._get(db,x[0]) for x in db.execute('SELECT id FROM ws_orders ORDER BY id DESC').fetchall()]
        return [x for x in rows if search.casefold() in raw(x).casefold()]
    def save_order(self,data,id_=None):
        self._allow('ATENDIMENTO','TECNICO','FINANCEIRO')
        if self.actor.get('role')=='FINANCEIRO' and (id_ is None or set(data)-{'receiver','final_checklist'}): raise PermissionError('Financeiro pode apenas registrar os dados de entrega.')
        with self.connect() as db: return self._save_order(db,data,id_)
    def _save_order(self,db,data,id_=None,parent=None):
        old=self._order(db,id_) if id_ is not None else None
        if old: self._editable(old)
        d=json.loads(old['data']) if old else {}
        cid=int(data.get('customer_id',old['customer_id'] if old else 0))
        customer=db.execute('SELECT data FROM customers WHERE id=?',(cid,)).fetchone()
        if not customer: raise ValueError('Selecione um cliente cadastrado.')
        if old and old['approved_cents'] is not None:
            if cid!=old['customer_id']: raise ValueError('Cliente aprovado não pode ser substituído.')
            for field in ('warranty_days','warranty_terms','approval_note'):
                if field in data and str(data[field])!=str(d.get(field,'')): raise ValueError('Condições aprovadas não podem ser alteradas.')
        for k in FIELDS:
            if k in data: d[k]=str(data[k]).strip()[:10000]
            elif k not in d: d[k]=''
        if not d['equipment']: raise ValueError('Informe o equipamento.')
        if d['due_date']: date.fromisoformat(d['due_date'])
        days=int(data.get('warranty_days',d.get('warranty_days',0)))
        if not 0<=days<=3650: raise ValueError('Prazo de garantia inválido.')
        d['warranty_days']=days
        if not old or cid!=old['customer_id']: d['customer']=dict(json.loads(customer[0]),id=cid)
        d['updated_at']=now()
        if old:
            db.execute('UPDATE ws_orders SET customer_id=?,data=? WHERE id=?',(cid,raw(d),id_))
        else:
            d['created_at']=now(); d['company']=self.store.company()
            id_=db.execute('INSERT INTO ws_orders(customer_id,status,data,parent_id) VALUES(?,?,?,?)',(cid,'RECEBIDA',raw(d),parent)).lastrowid
            d['number']=f'OS-{date.today().year}-{id_:06d}'
            db.execute('UPDATE ws_orders SET data=? WHERE id=?',(raw(d),id_))
        self._event(db,id_,'ATUALIZADA' if old else 'ABERTA')
        return id_
    def add_item(self,order_id,data):
        self._allow('ATENDIMENTO','TECNICO')
        with self.connect() as db:
            request=data.get('request_id') or None
            if request:
                existing=db.execute('SELECT id,order_id FROM ws_items WHERE request_id=?',(request,)).fetchone()
                if existing:
                    if existing['order_id']!=order_id: raise ValueError('Identificador já utilizado.')
                    return existing['id']
            self._editable(self._order(db,order_id),True)
            desc=str(data.get('description','')).strip(); kind=data.get('kind','SERVICO')
            units=qty(data.get('quantity','1')); price=scaled(data.get('price','0')); cost=scaled(data.get('cost','0'))
            if not desc or kind not in ('SERVICO','PECA') or units<=0 or min(price,cost)<0: raise ValueError('Item inválido.')
            part=data.get('part_id') or None
            if part and kind!='PECA': raise ValueError('Estoque exige item do tipo peça.')
            if part: self._move(db,int(part),-units,'CONSUMO',desc,order_id)
            total=int((Decimal(price)*units/1000).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
            d={'description':desc[:1000],'kind':kind,'quantity':quantity(units),'price_cents':price,'cost_cents':cost,'price':str(Decimal(price)/100),'cost':str(Decimal(cost)/100)}
            iid=db.execute('INSERT INTO ws_items(order_id,data,part_id,units,total_cents,request_id) VALUES(?,?,?,?,?,?)',(order_id,raw(d),part,units,total,request)).lastrowid
            self._event(db,order_id,'ITEM_ADICIONADO',item_id=iid,total_cents=total)
            return iid
    def remove_item(self,order_id,item_id):
        self._allow('ATENDIMENTO','TECNICO')
        with self.connect() as db:
            self._editable(self._order(db,order_id),True)
            i=db.execute('SELECT * FROM ws_items WHERE id=? AND order_id=?',(item_id,order_id)).fetchone()
            if not i: raise ValueError('Item não encontrado.')
            if self._total(db,order_id)-i['total_cents']<self._paid(db,order_id): raise ValueError('A remoção excederia o saldo recebido.')
            if i['part_id']: self._move(db,i['part_id'],i['units'],'DEVOLUCAO','Remoção de item',order_id)
            db.execute('DELETE FROM ws_items WHERE id=?',(item_id,)); self._event(db,order_id,'ITEM_REMOVIDO',item_id=item_id)
    def transition(self,order_id,status,note=''):
        self._allow('ATENDIMENTO','TECNICO','FINANCEIRO')
        graph={'RECEBIDA':('DIAGNOSTICO','CANCELADA'),'DIAGNOSTICO':('AGUARDANDO_APROVACAO','CANCELADA'),'AGUARDANDO_APROVACAO':('DIAGNOSTICO','AGUARDANDO_PECA','EM_REPARO','CANCELADA'),'AGUARDANDO_PECA':('EM_REPARO','CANCELADA'),'EM_REPARO':('AGUARDANDO_PECA','EM_TESTES','CANCELADA'),'EM_TESTES':('EM_REPARO','PRONTA'),'PRONTA':('EM_REPARO','ENTREGUE')}
        with self.connect() as db:
            r=self._order(db,order_id)
            if status==r['status']: return
            if status not in graph.get(r['status'],()): raise ValueError('Transição de situação não permitida.')
            d=json.loads(r['data']); approved=r['approved_cents']
            if status=='EM_REPARO' and approved is None:
                self._allow('ATENDIMENTO')
                if not note.strip(): raise ValueError('Registre responsável, canal e informação da aprovação.')
                approved=self._total(db,order_id); d['approval_note']=note; d['approved_at']=now()
            if status=='ENTREGUE':
                self._allow('ATENDIMENTO','FINANCEIRO')
                if not d.get('receiver') or not d.get('final_checklist'): raise ValueError('Informe recebedor e checklist final antes da entrega.')
                if self._total(db,order_id)>self._paid(db,order_id):
                    self._allow('FINANCEIRO')
                    if not note.strip(): raise ValueError('Justifique a entrega com saldo pendente.')
                d['delivered_at']=now(); d['warranty_until']=(date.today()+timedelta(days=d['warranty_days'])).isoformat()
            if status=='CANCELADA':
                self._allow('ATENDIMENTO')
                if self._paid(db,order_id): raise ValueError('Estorne os pagamentos antes de cancelar.')
                for i in db.execute('SELECT * FROM ws_items WHERE order_id=? AND part_id IS NOT NULL',(order_id,)).fetchall(): self._move(db,i['part_id'],i['units'],'DEVOLUCAO','Cancelamento da OS',order_id)
            db.execute('UPDATE ws_orders SET status=?,data=?,approved_cents=? WHERE id=?',(status,raw(d),approved,order_id))
            self._event(db,order_id,'SITUACAO',source=r['status'],target=status,note=note)
    def record_payment(self,order_id,data):
        self._allow('ATENDIMENTO','FINANCEIRO')
        with self.connect() as db:
            request=data.get('request_id') or None
            if request:
                p=db.execute('SELECT id,order_id FROM ws_payments WHERE request_id=?',(request,)).fetchone()
                if p:
                    if p['order_id']!=order_id: raise ValueError('Identificador já utilizado.')
                    return p['id']
            r=self._order(db,order_id)
            if r['status']=='CANCELADA' or r['approved_cents'] is None: raise ValueError('A OS deve estar aprovada para receber pagamentos.')
            amount=scaled(data.get('amount',0))
            if amount<=0 or amount>self._total(db,order_id)-self._paid(db,order_id): raise ValueError('Pagamento deve ser positivo e não exceder o saldo.')
            d={'method':str(data.get('method','')),'reference':str(data.get('reference','')),'created_at':now(),'actor':dict(self.actor)}
            pid=db.execute('INSERT INTO ws_payments(order_id,amount_cents,data,request_id) VALUES(?,?,?,?)',(order_id,amount,raw(d),request)).lastrowid
            self._cash(db,amount,dict(d,description=f'Recebimento OS {order_id}',kind='ENTRADA'),payment_id=pid)
            self._event(db,order_id,'PAGAMENTO',payment_id=pid,amount_cents=amount)
            return pid
    def reverse_payment(self,payment_id,reason):
        self._allow('FINANCEIRO')
        if not reason.strip(): raise ValueError('Informe o motivo do estorno.')
        with self.connect() as db:
            p=db.execute('SELECT * FROM ws_payments WHERE id=?',(payment_id,)).fetchone()
            if not p: raise ValueError('Pagamento não encontrado.')
            if p['reversed']: raise ValueError('Pagamento já estornado.')
            db.execute('UPDATE ws_payments SET reversed=1 WHERE id=?',(payment_id,))
            self._cash(db,-p['amount_cents'],{'kind':'SAIDA','description':'Estorno: '+reason,'method':json.loads(p['data']).get('method','')},payment_id=payment_id)
            self._event(db,p['order_id'],'ESTORNO',payment_id=payment_id,reason=reason)
    def create_return(self,order_id,reason):
        self._allow('ATENDIMENTO')
        if not reason.strip(): raise ValueError('Informe o motivo do retorno.')
        with self.connect() as db:
            o=self._get(db,order_id)
            if o['status']!='ENTREGUE': raise ValueError('Retorno exige OS entregue.')
            d={k:o.get(k,'') for k in ('customer_id','equipment','brand','model','serial','accessories')}; d['complaint']=reason
            nid=self._save_order(db,d,parent=order_id); self._event(db,order_id,'RETORNO',return_id=nid,reason=reason)
            return nid
    def list_parts(self):
        self._allow('ATENDIMENTO','TECNICO','FINANCEIRO')
        with self.connect() as db: return [dict(json.loads(r['data']),id=r['id'],quantity=quantity(r['stock']),stock_milli=r['stock']) for r in db.execute('SELECT * FROM ws_parts ORDER BY id DESC')]
    def save_part(self,data,id_=None):
        self._allow('ATENDIMENTO','FINANCEIRO')
        d={k:str(data.get(k,'')).strip()[:1000] for k in ('description','sku')}
        d.update(price_cents=scaled(data.get('price',0)),cost_cents=scaled(data.get('cost',0)),minimum=quantity(qty(data.get('minimum',0))))
        if not d['description'] or min(d['price_cents'],d['cost_cents'],qty(d['minimum']))<0: raise ValueError('Peça inválida.')
        with self.connect() as db:
            if id_ is None: return db.execute('INSERT INTO ws_parts(data) VALUES(?)',(raw(d),)).lastrowid
            if db.execute('UPDATE ws_parts SET data=? WHERE id=?',(raw(d),id_)).rowcount!=1: raise ValueError('Peça não encontrada.')
            return id_
    def _move(self,db,part,units,kind,note,order_id=None):
        if not units or not note.strip(): raise ValueError('Informe quantidade e justificativa.')
        if db.execute('UPDATE ws_parts SET stock=stock+? WHERE id=? AND stock+?>=0',(units,part,units)).rowcount!=1: raise ValueError('Peça inexistente ou estoque insuficiente.')
        return db.execute('INSERT INTO ws_movements(part_id,quantity,kind,note,order_id,created_at,actor) VALUES(?,?,?,?,?,?,?)',(part,units,kind,note,order_id,now(),raw(self.actor))).lastrowid
    def stock_move(self,part_id,quantity,kind,note,order_id=None):
        self._allow('ATENDIMENTO','FINANCEIRO')
        units=qty(quantity)
        if kind not in ('ENTRADA','SAIDA','AJUSTE','DEVOLUCAO'): raise ValueError('Tipo de movimento inválido.')
        if kind in ('ENTRADA','DEVOLUCAO') and units<=0: raise ValueError('Entrada deve ser positiva.')
        if kind=='SAIDA': units=-abs(units)
        with self.connect() as db: return self._move(db,part_id,units,kind,note,order_id)
    def list_movements(self):
        self._allow('ATENDIMENTO','FINANCEIRO')
        with self.connect() as db: return [dict(dict(r),quantity=quantity(r['quantity'])) for r in db.execute('SELECT * FROM ws_movements ORDER BY id DESC')]
    def list_suppliers(self):
        self._allow('ATENDIMENTO','FINANCEIRO')
        with self.connect() as db: return [dict(json.loads(r['data']),id=r['id']) for r in db.execute('SELECT * FROM ws_suppliers ORDER BY id DESC')]
    def save_supplier(self,data,id_=None):
        self._allow('ATENDIMENTO','FINANCEIRO')
        d={k:str(data.get(k,'')).strip()[:1000] for k in ('name','document','phone','email','address')}
        if not d['name']: raise ValueError('Informe o nome.')
        with self.connect() as db:
            if id_ is None: return db.execute('INSERT INTO ws_suppliers(data) VALUES(?)',(raw(d),)).lastrowid
            if db.execute('UPDATE ws_suppliers SET data=? WHERE id=?',(raw(d),id_)).rowcount!=1: raise ValueError('Fornecedor não encontrado.')
            return id_
    def list_accounts(self):
        self._allow('FINANCEIRO')
        with self.connect() as db: return [dict(json.loads(r['data']),id=r['id'],amount_cents=r['amount_cents'],settled=bool(r['settled'])) for r in db.execute('SELECT * FROM ws_accounts ORDER BY id DESC')]
    def save_account(self,data):
        self._allow('FINANCEIRO'); amount=scaled(data.get('amount',0)); kind=data.get('kind')
        if amount<=0 or kind not in ('PAGAR','RECEBER') or not str(data.get('description','')).strip(): raise ValueError('Conta inválida.')
        if data.get('due_date'): date.fromisoformat(data['due_date'])
        d={k:str(data.get(k,'')) for k in ('description','kind','due_date')}; d.update(created_at=now(),actor=dict(self.actor))
        with self.connect() as db: return db.execute('INSERT INTO ws_accounts(data,amount_cents) VALUES(?,?)',(raw(d),amount)).lastrowid
    def settle_account(self,id,method=''):
        self._allow('FINANCEIRO')
        with self.connect() as db:
            a=db.execute('SELECT * FROM ws_accounts WHERE id=?',(id,)).fetchone()
            if not a or a['settled']: raise ValueError('Conta inexistente ou já liquidada.')
            d=json.loads(a['data']); d.update(settled_at=now(),method=method)
            db.execute('UPDATE ws_accounts SET settled=1,data=? WHERE id=?',(raw(d),id))
            self._cash(db,a['amount_cents']*(1 if d['kind']=='RECEBER' else -1),dict(d,kind='ENTRADA' if d['kind']=='RECEBER' else 'SAIDA'),account_id=id)
    def _cash(self,db,amount,data,payment_id=None,account_id=None):
        d=dict(data,created_at=now(),actor=dict(self.actor))
        return db.execute('INSERT INTO ws_cash(data,amount_cents,payment_id,account_id) VALUES(?,?,?,?)',(raw(d),amount,payment_id,account_id)).lastrowid
    def cash_entry(self,data):
        self._allow('FINANCEIRO'); amount=scaled(data.get('amount',0)); kind=data.get('kind')
        if amount<=0 or kind not in ('ENTRADA','SAIDA') or not str(data.get('description','')).strip(): raise ValueError('Lançamento inválido.')
        with self.connect() as db: return self._cash(db,amount*(1 if kind=='ENTRADA' else -1),{k:str(data.get(k,'')) for k in ('description','kind','method')})
    def list_cash(self):
        self._allow('FINANCEIRO')
        with self.connect() as db: return [dict(json.loads(r['data']),id=r['id'],amount_cents=r['amount_cents'],payment_id=r['payment_id'],account_id=r['account_id']) for r in db.execute('SELECT * FROM ws_cash ORDER BY id DESC')]
    def report(self):
        self._allow('FINANCEIRO')
        orders=self.list_orders(); parts=self.list_parts()
        results=[{'id':o['id'],'number':o['number'],'technician':o.get('technician',''),'total_cents':o['total_cents'],'cost_cents':sum(int((Decimal(i['cost_cents'])*qty(i['quantity'])/1000).quantize(Decimal('1'),rounding=ROUND_HALF_UP)) for i in o['items'])} for o in orders if o['status']!='CANCELADA']
        for result in results: result['margin_cents']=result['total_cents']-result['cost_cents']
        return {'order_results':results,'orders_by_status':{s:sum(o['status']==s for o in orders) for s in STATUSES},'received_cents':sum(o['paid_cents'] for o in orders),'balance_cents':sum(o['balance_cents'] for o in orders if o['status']!='CANCELADA'),'stock_value_cents':sum(int(Decimal(p['cost_cents'])*p['stock_milli']/1000) for p in parts),'low_stock':[p for p in parts if p['stock_milli']<=qty(p['minimum'])],'overdue':[o for o in orders if o.get('due_date') and o['due_date']<date.today().isoformat() and o['status'] not in ('ENTREGUE','CANCELADA')]}
    def add_attachment(self,order_id,path):
        self._allow('ATENDIMENTO','TECNICO'); p=Path(path)
        with p.open('rb') as f: content=f.read(10*1024*1024+1)
        if len(content)>10*1024*1024: raise ValueError('Anexo excede 10 MB.')
        with self.connect() as db:
            self._editable(self._order(db,order_id))
            aid=db.execute('INSERT INTO ws_attachments(order_id,filename,content,created_at) VALUES(?,?,?,?)',(order_id,p.name,content,now())).lastrowid
            self._event(db,order_id,'ANEXO',filename=p.name,attachment_id=aid); return aid
    def attachment_bytes(self,id):
        self._allow('ATENDIMENTO','TECNICO','FINANCEIRO')
        with self.connect() as db:
            r=db.execute('SELECT filename,content FROM ws_attachments WHERE id=?',(id,)).fetchone()
            if not r: raise ValueError('Anexo não encontrado.')
            return r['filename'],bytes(r['content'])

def _validate_workshop_database(db):
    """Validate additional schema without modifying the source database."""
    tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    marker=db.execute("SELECT value FROM meta WHERE key='workshop_schema'").fetchone()
    present=set(TABLES)&tables
    if not present and not marker: return
    if present!=set(TABLES) or not marker or marker[0]!='1': raise ValueError('Estrutura de assistência incompatível.')
    if db.execute('PRAGMA foreign_key_check').fetchone(): raise ValueError('Referência inválida.')
    numbers=set()
    for r in db.execute('SELECT id,status,data,approved_cents,customer_id FROM ws_orders'):
        oid,status,data,approved,cid=r; d=json.loads(data)
        if status not in STATUSES or not isinstance(d,dict) or not d.get('equipment') or not d.get('number'): raise ValueError('OS inválida.')
        if d['number'] in numbers: raise ValueError('Numeração duplicada.')
        numbers.add(d['number'])
        if any(k not in d or not isinstance(d[k],str) for k in FIELDS): raise ValueError('Dados de OS incompletos.')
        customer=d.get('customer')
        if not isinstance(customer,dict) or customer.get('id')!=cid or not customer.get('name'): raise ValueError('Cliente da OS inconsistente.')
        if not isinstance(d.get('company'),dict): raise ValueError('Empresa inválida.')
        if type(d.get('warranty_days')) is not int or not 0<=d['warranty_days']<=3650: raise ValueError('Garantia inválida.')
        for k in ('created_at','updated_at'): datetime.fromisoformat(d[k])
        if d['due_date']: date.fromisoformat(d['due_date'])
        if status in ('EM_REPARO','EM_TESTES','PRONTA','ENTREGUE') and approved is None: raise ValueError('Aprovação ausente.')
        if status=='ENTREGUE':
            if not d['receiver'] or not d['final_checklist']: raise ValueError('Entrega incompleta.')
            datetime.fromisoformat(d['delivered_at']); date.fromisoformat(d['warranty_until'])
        total=db.execute('SELECT COALESCE(SUM(total_cents),0) FROM ws_items WHERE order_id=?',(oid,)).fetchone()[0]
        paid=db.execute('SELECT COALESCE(SUM(amount_cents),0) FROM ws_payments WHERE order_id=? AND reversed=0',(oid,)).fetchone()[0]
        if paid<0 or paid>total or (paid and approved is None) or (status=='CANCELADA' and paid) or (approved is not None and (type(approved) is not int or approved!=total)): raise ValueError('Totais inconsistentes.')
    for data,units,total in db.execute('SELECT data,units,total_cents FROM ws_items'):
        d=json.loads(data)
        if not d.get('description') or d.get('kind') not in ('SERVICO','PECA') or type(d.get('price_cents')) is not int or type(d.get('cost_cents')) is not int or min(d['price_cents'],d['cost_cents'])<0 or scaled(d['cost'])!=d['cost_cents']: raise ValueError('Dados de item inválidos.')
        if units<=0 or total<0 or qty(d['quantity'])!=units or scaled(d['price'])!=d['price_cents'] or int((Decimal(d['price_cents'])*units/1000).quantize(Decimal('1'),rounding=ROUND_HALF_UP))!=total: raise ValueError('Item inconsistente.')
    for pid,stock,data in db.execute('SELECT id,stock,data FROM ws_parts'):
        if stock<0 or stock!=db.execute('SELECT COALESCE(SUM(quantity),0) FROM ws_movements WHERE part_id=?',(pid,)).fetchone()[0]: raise ValueError('Estoque inconsistente.')
        part=json.loads(data)
        if not part.get('description') or min(part['price_cents'],part['cost_cents'],qty(part['minimum']))<0: raise ValueError('Cadastro de peça inválido.')
    for pid,amount,reversed_ in db.execute('SELECT id,amount_cents,reversed FROM ws_payments'):
        if amount<=0 or reversed_ not in (0,1) or db.execute('SELECT COALESCE(SUM(amount_cents),0) FROM ws_cash WHERE payment_id=?',(pid,)).fetchone()[0] != (0 if reversed_ else amount): raise ValueError('Pagamento inconsistente.')
    for aid,data,amount,settled in db.execute('SELECT id,data,amount_cents,settled FROM ws_accounts'):
        d=json.loads(data)
        if amount<=0 or d['kind'] not in ('PAGAR','RECEBER') or settled not in (0,1) or not d.get('description'): raise ValueError('Conta inválida.')
        if d.get('due_date'): date.fromisoformat(d['due_date'])
        datetime.fromisoformat(d['created_at'])
        expected=amount*(1 if d['kind']=='RECEBER' else -1) if settled else 0
        if db.execute('SELECT COALESCE(SUM(amount_cents),0) FROM ws_cash WHERE account_id=?',(aid,)).fetchone()[0]!=expected: raise ValueError('Liquidação inconsistente.')
    for table in ('ws_events','ws_suppliers','ws_cash','ws_payments'):
        for data, in db.execute(f'SELECT data FROM {table}'):
            d=json.loads(data)
            if not isinstance(d,dict): raise ValueError('Registro inválido.')
            if table=='ws_suppliers':
                if not d.get('name') or any(not isinstance(d.get(k),str) for k in ('name','document','phone','email','address')): raise ValueError('Fornecedor inválido.')
            else:
                datetime.fromisoformat(d['created_at'])
                if not isinstance(d.get('actor'),dict) or not d['actor'].get('name') or not d['actor'].get('role'): raise ValueError('Auditoria inválida.')
            if table=='ws_events' and not isinstance(d.get('action'),str): raise ValueError('Evento inválido.')
            if table=='ws_payments' and any(not isinstance(d.get(k),str) for k in ('method','reference')): raise ValueError('Recebimento inválido.')
            if table=='ws_cash' and (not d.get('description') or d.get('kind') not in ('ENTRADA','SAIDA')): raise ValueError('Caixa inválido.')
    for data,amount,payment,account in db.execute('SELECT data,amount_cents,payment_id,account_id FROM ws_cash'):
        d=json.loads(data)
        if type(amount) is not int or amount==0 or (amount>0)!=(d['kind']=='ENTRADA') or (payment is not None and account is not None): raise ValueError('Lançamento de caixa inconsistente.')
    for units,kind,note,created,actor in db.execute('SELECT quantity,kind,note,created_at,actor FROM ws_movements'):
        if type(units) is not int or units==0 or not note or kind not in ('ENTRADA','SAIDA','AJUSTE','DEVOLUCAO','CONSUMO'): raise ValueError('Movimento inválido.')
        if kind in ('ENTRADA','DEVOLUCAO') and units<=0 or kind in ('SAIDA','CONSUMO') and units>=0: raise ValueError('Sinal do movimento inválido.')
        datetime.fromisoformat(created)
        if not isinstance(json.loads(actor),dict): raise ValueError('Autor do movimento inválido.')
    for name,size in db.execute('SELECT filename,length(content) FROM ws_attachments'):
        if not name or Path(name).name!=name or size>10*1024*1024: raise ValueError('Anexo inválido.')


def validate_workshop_database(db):
    try:
        _validate_workshop_database(db)
    except (KeyError, TypeError, IndexError, OverflowError, InvalidOperation, sqlite3.Error) as exc:
        raise ValueError('Estrutura ou dados de assistência inválidos.') from exc
