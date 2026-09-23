"""Validação completa do conteúdo antes de substituir um banco de trabalho."""
import json
from datetime import date
from .domain import calculate, STATUSES, line_total, number


def strings(data,keys):
    if not isinstance(data,dict) or any(not isinstance(data.get(k),str) for k in keys):
        raise ValueError('Estrutura de backup inválida.')


def validate_database(db):
    expected={'meta':{'key','value'},'customers':{'id','data'},'catalog':{'id','data'},'quotes':{'id','data'}}
    for table,columns in expected.items():
        kind=db.execute('SELECT type FROM sqlite_master WHERE name=?',(table,)).fetchone()
        if kind!=('table',):raise ValueError('Tabela ausente no backup.')
        if {row[1] for row in db.execute(f'PRAGMA table_info({table})')}!=columns:raise ValueError('Colunas incompatíveis.')
    if db.execute("SELECT value FROM meta WHERE key='schema'").fetchone()!=('1',):raise ValueError('Versão incompatível.')
    company=db.execute("SELECT value FROM meta WHERE key='company'").fetchone()
    if company:strings(json.loads(company[0]),('name','document','phone','email','address','terms'))
    ids=set()
    for id_,raw in db.execute('SELECT id,data FROM customers'):
        customer=json.loads(raw);strings(customer,('name','document','phone','email','address'))
        if type(id_) is not int or id_<1 or not customer['name'].strip():raise ValueError()
        ids.add(id_)
    for id_,raw in db.execute('SELECT id,data FROM catalog'):
        item=json.loads(raw);strings(item,('description','unit','kind'))
        if not item['description'].strip() or item['kind'] not in ('PRODUTO','SERVIÇO') or type(item.get('price_cents')) is not int or not 0<=item['price_cents']<=100000000000:raise ValueError()
    numbers=set()
    for id_,raw in db.execute('SELECT id,data FROM quotes'):
        q=json.loads(raw);strings(q,('number','created_at','valid_until','status','discount','notes','terms'))
        if q['number'] in numbers or not q['number'] or q['status'] not in STATUSES or q.get('customer_id') not in ids:raise ValueError()
        numbers.add(q['number']);date.fromisoformat(q['created_at']);date.fromisoformat(q['valid_until'])
        strings(q.get('customer'),('name','document','phone','email','address'))
        if q['customer'].get('id')!=q['customer_id']:raise ValueError()
        items=q.get('items')
        if not isinstance(items,list) or not 1<=len(items)<=500:raise ValueError()
        for item in items:
            strings(item,('description','quantity','price','unit'))
            if not item['description'].strip() or type(item.get('total_cents')) is not int or line_total(item)!=item['total_cents']:raise ValueError()
        totals=calculate(items,q['discount'])
        for key,total in zip(('subtotal_cents','discount_cents','total_cents'),totals):
            if type(q.get(key)) is not int or q[key]!=total:raise ValueError()

    from .workshop import validate_workshop_database
    from .users import validate_users_database
    validate_workshop_database(db)
    validate_users_database(db)
    from .finance_extras import validate_finance_database
    validate_finance_database(db)
