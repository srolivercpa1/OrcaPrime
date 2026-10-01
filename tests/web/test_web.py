import os
import pytest
pytest.importorskip("sqlalchemy")
from fastapi.testclient import TestClient

@pytest.fixture
def env(tmp_path):
    from webapp.api import create_app
    from webapp.security import bootstrap
    url=os.environ.get('ORCAPRIME_TEST_DATABASE') or 'sqlite:///'+str(tmp_path/'web.db')
    if os.environ.get('ORCAPRIME_TEST_DATABASE'):
        from sqlalchemy import create_engine
        from webapp.db import Base
        engine=create_engine(url);Base.metadata.drop_all(engine);engine.dispose()
    bootstrap(url,'owner@example.com','Owner-password-123')
    app=create_app(url)
    owner=TestClient(app)
    assert owner.post('/api/login',json={'email':'owner@example.com','password':'Owner-password-123'}).status_code==200
    owner.headers['X-CSRF-Token']=owner.get('/api/me').json()['csrf']
    return app, owner

def company(owner,name,email):
    r=owner.post('/api/companies',json={'name':name,'email':email,'password':'Tenant-password-123','days':30})
    assert r.status_code==200,r.text
    return r.json()

def login(app,email):
    c=TestClient(app)
    r=c.post('/api/login',json={'email':email,'password':'Tenant-password-123'})
    assert r.status_code==200,r.text
    c.headers['X-CSRF-Token']=r.json()['csrf']
    return c

def test_sessions_isolation_and_suspension(env):
    app,owner=env
    a=company(owner,'Loja A','a@example.com'); company(owner,'Loja B','b@example.com')
    ca=login(app,'a@example.com'); cb=login(app,'b@example.com')
    assert TestClient(app).get('/api/customers').status_code==401
    assert ca.post('/api/companies',json={'name':'Fraude','email':'x@example.com','password':'Tenant-password-123','days':30}).status_code==403
    row=ca.post('/api/customers',json={'name':'Mateus','phone':'64999999999'}).json()
    assert cb.get('/api/customers').json()==[]
    assert cb.delete('/api/customers/'+row['id']).status_code==404
    ca.headers.pop('X-CSRF-Token')
    assert ca.post('/api/customers',json={'name':'CSRF'}).status_code==403
    assert owner.patch('/api/companies/'+a['id'],json={'active':False}).status_code==200
    assert ca.get('/api/dashboard').status_code==401
    assert ca.post('/api/login',json={'email':'a@example.com','password':'Tenant-password-123'}).status_code==403

def test_user_revocation(env):
    app,owner=env; company(owner,'Loja','a@example.com'); admin=login(app,'a@example.com')
    r=admin.post('/api/users',json={'name':'Técnico','email':'tech@example.com','password':'Tenant-password-123','role':'TECNICO'})
    assert r.status_code==200,r.text
    tech=login(app,'tech@example.com')
    assert tech.delete('/api/users/'+r.json()['id']).status_code==403
    assert admin.patch('/api/users/'+r.json()['id'],json={'active':False}).status_code==200
    assert tech.get('/api/orders').status_code==401
    assert admin.delete('/api/users/'+admin.get('/api/me').json()['id']).status_code==409

def test_workshop_lifecycle_and_documents(env):
    app,owner=env; company(owner,'Loja A','a@example.com'); company(owner,'Loja B','b@example.com')
    a=login(app,'a@example.com'); b=login(app,'b@example.com')
    customer=a.post('/api/customers',json={'name':'Mateus','phone':'64999999999'}).json()
    assert a.post('/api/orders',json={'customer_id':'missing','device':'iPhone'}).status_code==404
    part=a.post('/api/parts',json={'name':'Bateria iPhone','quantity':2,'price':10000}).json()
    quote=a.post('/api/quotes',json={'customer_id':customer['id'],'device':'iPhone 13','description':'Troca de bateria','amount':18000}).json()
    r=a.post('/api/quotes/'+quote['id']+'/convert')
    assert r.status_code==200,r.text
    order=r.json(); oid=order['id']
    assert a.post('/api/quotes/'+quote['id']+'/convert').json()['id']==oid
    assert b.get('/api/orders/'+oid+'/document').status_code==404
    assert a.post('/api/orders/'+oid+'/consume',json={'part_id':part['id'],'quantity':1,'key':'consumo-123'}).status_code==200
    a.post('/api/orders/'+oid+'/consume',json={'part_id':part['id'],'quantity':1,'key':'consumo-123'})
    assert a.get('/api/parts').json()[0]['quantity']==1
    assert a.patch('/api/orders/'+oid,json={'status':'ENTREGUE'}).status_code==409
    assert a.patch('/api/orders/'+oid,json={'status':'EM_ANDAMENTO'}).status_code==200
    assert a.patch('/api/orders/'+oid,json={'status':'PRONTO','service':'Bateria substituída'}).status_code==200
    assert a.patch('/api/orders/'+oid,json={'status':'ENTREGUE'}).status_code==200
    assert a.get('/api/orders').json()[0]['delivered_at']
    pdf=a.get('/api/orders/'+oid+'/document?type=garantia')
    assert pdf.status_code==200 and pdf.content.startswith(b'%PDF')
    assert a.get('/api/dashboard').json()['delivered']==1
    assert a.delete('/api/customers/'+customer['id']).status_code==200
    assert a.get('/api/orders').json()==[]
    assert a.get('/api/parts').json()[0]['quantity']==1 # completed repairs keep consumed stock

def test_validation_and_photo_isolation(env):
    import io
    from PIL import Image
    app,owner=env; company(owner,'A loja','a@example.com'); company(owner,'B loja','b@example.com')
    a=login(app,'a@example.com'); b=login(app,'b@example.com')
    assert a.post('/api/customers',json={'name':'','company_id':'forged'}).status_code==422
    c=a.post('/api/customers',json={'name':'Maria'}).json()
    o=a.post('/api/orders',json={'customer_id':c['id'],'device':'Samsung','description':'Tela trincada'}).json()
    assert a.post('/api/parts',json={'name':'Tela','quantity':-1}).status_code==422
    assert a.post('/api/orders/'+o['id']+'/photos',files={'file':('x.html',b'<html>bad</html>','image/png')}).status_code==422
    out=io.BytesIO();Image.new('RGB',(20,20),'blue').save(out,'PNG')
    r=a.post('/api/orders/'+o['id']+'/photos',files={'file':('tela.png',out.getvalue(),'image/png')})
    assert r.status_code==200,r.text
    url=r.json()['url'];assert a.get(url).headers['content-type']=='image/jpeg'
    assert b.get(url).status_code==404
    assert a.post('/api/orders/'+o['id']+'/consume',json={'part_id':'invalid','quantity':1,'key':'x'}).status_code==404

def test_finance_and_permissions(env):
    app,owner=env;company(owner,'Loja','a@example.com');a=login(app,'a@example.com')
    a.post('/api/users',json={'name':'Técnico','email':'tech@example.com','password':'Tenant-password-123','role':'TECNICO'})
    tech=login(app,'tech@example.com')
    assert tech.get('/api/entries').status_code==403
    e=a.post('/api/entries',json={'name':'Aluguel','direction':'SAIDA','amount':10000,'due':'2026-10-10'}).json()
    assert a.patch('/api/entries/'+e['id'],json={'paid':True}).status_code==200
    assert a.get('/api/dashboard').json()['balance']==-10000
    assert a.delete('/api/entries/'+e['id']).status_code==409

def test_backup_restore(env,tmp_path):
    from webapp.backup import backup,restore
    from webapp.api import create_app
    app,owner=env; company(owner,'Restaurada','a@example.com');a=login(app,'a@example.com')
    a.post('/api/customers',json={'name':'Cliente preservado'})
    target=backup(app.state.engine,str(tmp_path/'backup'))
    assert target.suffix=='.gz'
    url='sqlite:///'+str(tmp_path/'restored.db')
    restore(url,str(target))
    restored=login(create_app(url),'a@example.com')
    assert restored.get('/api/customers').json()[0]['name']=='Cliente preservado'
    with pytest.raises(ValueError):restore(url,str(target))

def test_password_change_and_origin(env):
    app,owner=env; company(owner,'Loja','a@example.com');a=login(app,'a@example.com')
    assert a.post('/api/customers',json={'name':'Ataque'},headers={'Origin':'https://evil.example'}).status_code==403
    assert a.post('/api/password',json={'current':'wrong','password':'Brand-new-password-123'}).status_code==401
    assert a.post('/api/password',json={'current':'Tenant-password-123','password':'Brand-new-password-123'}).status_code==200
    assert a.get('/api/me').status_code==401
    assert TestClient(app).post('/api/login',json={'email':'a@example.com','password':'Brand-new-password-123'}).status_code==200

def test_finance_dashboard_does_not_leak_order_details(env):
    app,owner=env;company(owner,'Loja','a@example.com');a=login(app,'a@example.com')
    c=a.post('/api/customers',json={'name':'Cliente'}).json()
    a.post('/api/orders',json={'customer_id':c['id'],'device':'Aparelho','serial':'PRIVATE-IMEI','description':'PRIVATE-NOTES'})
    a.post('/api/users',json={'name':'Financeiro','email':'fin@example.com','password':'Tenant-password-123','role':'FINANCEIRO'})
    f=login(app,'fin@example.com');r=f.get('/api/dashboard')
    assert r.status_code==200
    assert r.json()['recent']==[]
    assert 'PRIVATE-' not in r.text

def test_customer_deletion_preview(env):
    app,owner=env;company(owner,'Loja','a@example.com');a=login(app,'a@example.com')
    c=a.post('/api/customers',json={'name':'Cliente'}).json()
    o=a.post('/api/orders',json={'customer_id':c['id'],'device':'iPhone'}).json()
    r=a.get('/api/customers/'+c['id']+'/deletion-preview')
    assert r.status_code==200,r.text
    assert r.json()['orders'][0]['id']==o['id']
    key=r.json()['fingerprint']
    a.post('/api/orders',json={'customer_id':c['id'],'device':'Samsung'})
    assert a.delete('/api/customers/'+c['id']+'?expected='+key).status_code==409
    assert len(a.get('/api/orders').json())==2

@pytest.mark.skipif(not os.environ.get('ORCAPRIME_TEST_DATABASE'),reason='PostgreSQL concurrency test')
def test_concurrent_reciprocal_revocation_preserves_admin(env):
    from concurrent.futures import ThreadPoolExecutor
    import threading
    from sqlalchemy import event,select
    from webapp.db import User
    app,owner=env;company(owner,'Loja','a@example.com');a=login(app,'a@example.com')
    buser=a.post('/api/users',json={'name':'Outro admin','email':'b@example.com','password':'Tenant-password-123','role':'ADMIN'}).json()
    b=login(app,'b@example.com');aid=a.get('/api/me').json()['id']
    barrier=threading.Barrier(2)
    def before(conn,cursor,statement,parameters,context,executemany):
        if 'web_companies' in statement and 'FOR UPDATE' in statement:barrier.wait(timeout=10)
    event.listen(app.state.engine,'before_cursor_execute',before)
    try:
        with ThreadPoolExecutor(2) as pool:
            fa=pool.submit(a.patch,'/api/users/'+buser['id'],json={'active':False})
            fb=pool.submit(b.patch,'/api/users/'+aid,json={'active':False})
            results=[fa.result().status_code,fb.result().status_code]
        assert sorted(results)==[200,401]
    finally:event.remove(app.state.engine,'before_cursor_execute',before)
    with app.state.factory() as db:
        assert len(list(db.scalars(select(User).where(User.role=='ADMIN',User.active==True))))==1
