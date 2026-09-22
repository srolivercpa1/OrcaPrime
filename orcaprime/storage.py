import json
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from .domain import calculate, money, number, STATUSES, line_total, decimal_text

class Store:
    def __init__(self, path):
        self.path = Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
            INSERT OR IGNORE INTO meta VALUES('schema','1');
            CREATE TABLE IF NOT EXISTS customers(id INTEGER PRIMARY KEY, data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS catalog(id INTEGER PRIMARY KEY, data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS quotes(id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT NOT NULL);
            ''')

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=15)
        try:
            with db: yield db
        finally: db.close()

    def _list(self,table):
        with self.connect() as db:
            return [dict(json.loads(data),id=id_) for id_,data in db.execute(f'SELECT id,data FROM {table} ORDER BY id DESC')]

    def _save(self,table,data,id_=None):
        with self.connect() as db:
            raw=json.dumps(data,ensure_ascii=False)
            if id_ is not None:
                if db.execute(f'UPDATE {table} SET data=? WHERE id=?',(raw,id_)).rowcount!=1:
                    raise ValueError('Registro não encontrado.')
                return id_
            return db.execute(f'INSERT INTO {table}(data) VALUES(?)',(raw,)).lastrowid

    def list_customers(self): return self._list('customers')
    def list_items(self): return self._list('catalog')

    def save_customer(self,data,id_=None):
        clean={k:str(data.get(k,'')).strip()[:1000] for k in ('name','document','phone','email','address')}
        if not clean['name']: raise ValueError('Informe o nome do cliente.')
        return self._save('customers',clean,id_)

    def save_item(self,data,id_=None):
        clean={k:str(data.get(k,'')).strip()[:1000] for k in ('description','unit','kind')}
        if not clean['description']: raise ValueError('Informe a descrição.')
        if clean['kind'] not in ('PRODUTO','SERVIÇO'): raise ValueError('Tipo inválido.')
        clean['price_cents']=money(data['price'])
        return self._save('catalog',clean,id_)

    def company(self):
        with self.connect() as db:
            row=db.execute("SELECT value FROM meta WHERE key='company'").fetchone()
        return json.loads(row[0]) if row else {}

    def save_company(self,data):
        clean={k:str(data.get(k,'')).strip()[:2000] for k in ('name','document','phone','email','address','terms')}
        if not clean['name']: raise ValueError('Informe o nome da empresa.')
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO meta VALUES(?,?)',('company',json.dumps(clean,ensure_ascii=False)))

    def get_quote(self,id_):
        with self.connect() as db: row=db.execute('SELECT data FROM quotes WHERE id=?',(id_,)).fetchone()
        if not row: raise ValueError('Orçamento não encontrado.')
        return dict(json.loads(row[0]),id=id_)

    def save_quote(self,data,id_=None,source_id=None):
        previous=self.get_quote(id_) if id_ else None
        source=self.get_quote(source_id) if source_id and not id_ else None
        cid=int(data['customer_id'])
        if previous and previous['customer_id']==cid:
            customer=previous['customer']
        elif source and source['customer_id']==cid:
            customer=source['customer']
        else:
            customer=next((c for c in self.list_customers() if c['id']==cid),None)
        if not customer: raise ValueError('Selecione um cliente cadastrado.')
        date.fromisoformat(data['valid_until'])
        status=data.get('status','RASCUNHO')
        if status not in STATUSES: raise ValueError('Situação inválida.')
        if len(data['items'])>500: raise ValueError('Limite de 500 itens por orçamento.')
        sub,disc,total=calculate(data['items'],data.get('discount',0))
        items=[]
        for i in data['items']:
            desc=str(i['description']).strip()
            if not desc or len(desc)>1000: raise ValueError('Descrição obrigatória, até 1.000 caracteres.')
            items.append({'description':desc,'unit':str(i.get('unit','un'))[:20],
                          'quantity':str(number(i['quantity'])),'price':str(money(i['price'])/100),
                          'total_cents':line_total(i)})
        q={'customer_id':cid,'customer':customer,'valid_until':data['valid_until'],'status':status,
           'items':items,'subtotal_cents':sub,'discount_cents':disc,'discount':str(disc/100),'total_cents':total,
           'notes':str(data.get('notes',''))[:10000],'terms':str(data.get('terms',''))[:10000],
           'created_at':previous['created_at'] if previous else date.today().isoformat()}
        with self.connect() as db:
            if previous:
                q['number']=previous['number']
                db.execute('UPDATE quotes SET data=? WHERE id=?',(json.dumps(q,ensure_ascii=False),id_))
            else:
                id_=db.execute("INSERT INTO quotes(data) VALUES('{}')").lastrowid
                q['number']=f'{date.today().year}-{id_:05d}'
                db.execute('UPDATE quotes SET data=? WHERE id=?',(json.dumps(q,ensure_ascii=False),id_))
        return id_

    def list_quotes(self,search=''):
        return [q for q in self._list('quotes') if search.casefold() in (q['number']+' '+q['customer']['name']+' '+q['status']).casefold()]

    def set_status(self,id_,status):
        if status not in STATUSES: raise ValueError('Situação inválida.')
        q=self.get_quote(id_); q.pop('id'); q['status']=status
        self._save('quotes',q,id_)

    def backup(self,destination):
        if Path(destination).resolve()==self.path.resolve(): raise ValueError('Escolha outro arquivo para o backup.')
        with self.connect() as src, sqlite3.connect(destination) as dst: src.backup(dst)

    def restore(self,source):
        source=Path(source)
        if source.resolve()==self.path.resolve(): raise ValueError('Selecione um arquivo de backup diferente.')
        try:
            uri=source.resolve().as_uri()+'?mode=ro'
            with sqlite3.connect(uri,uri=True) as src:
                if src.execute('PRAGMA integrity_check').fetchone()[0]!='ok': raise ValueError()
                from .backup_validation import validate_database
                validate_database(src)
                self.backup(self.path.with_name('antes-restauracao-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.db'))
                with self.connect() as dst: src.backup(dst)
        except (sqlite3.Error,ValueError,OSError,TypeError,KeyError,OverflowError):
            raise ValueError('Backup inválido, incompatível ou inacessível. O banco atual foi preservado.') from None
