import base64
from concurrent.futures import ThreadPoolExecutor
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient
from licensing.service import LicenseService, LicenseError
from licensing.security import password_hash
from licensing.api import create_app
from orcaprime.license_client import format_code, mask_code, verify_envelope

@pytest.fixture
def svc(tmp_path):
    return LicenseService(tmp_path/'licenses.db',Ed25519PrivateKey.generate(),b'x'*32)

def test_format_and_mask():
    assert format_code('ab23 cd45 ef67 gh89 jk23')=='AB23-CD45-EF67-GH89-JK23'
    assert mask_code('AB23-CD45-EF67-GH89-JK23')=='AB**-****-****-****-**23'
    assert len(format_code('A'*40))==24
    assert format_code('IO01@')==''

def test_activation_idempotent_limit_and_signature(svc):
    lic=svc.create('PRO',30,1)
    assert len(lic['code'])==24
    first=svc.activate(lic['code'],'device-1234567890','nonce-1234567890')
    again=svc.activate(lic['code'],'device-1234567890','nonce-1234567891')
    assert svc.get(lic['id'])['activation_count']==1
    public=svc.signing_key.public_key()
    payload=verify_envelope(first,public,'device-1234567890','nonce-1234567890')
    assert payload['plan']=='PRO'
    with pytest.raises(ValueError): verify_envelope(first,public,'other-device-123','nonce-1234567890')
    with pytest.raises(ValueError): verify_envelope(first,public,'device-1234567890','replayed-nonce')
    altered=dict(first); altered['signature']=base64.b64encode(b'x'*64).decode()
    with pytest.raises(ValueError): verify_envelope(altered,public,'device-1234567890','nonce-1234567890')
    with pytest.raises(LicenseError,match='Limite'): svc.activate(lic['code'],'device-2234567890','nonce-1234567890')
    # Reactivation rotates credentials, preventing an old stolen token from remaining valid.
    with pytest.raises(LicenseError): svc.validate(payload['device_token'],'device-1234567890','nonce-1234567890')
    token=verify_envelope(again,public,'device-1234567890','nonce-1234567891')['device_token']
    assert svc.validate(token,'device-1234567890','nonce-1234567892')['signature']

def test_block_cancel_expire_renew(svc):
    lic=svc.create('EMPRESA',30,2)
    envelope=svc.activate(lic['code'],'device-1234567890','nonce-1234567890')
    token=verify_envelope(envelope,svc.signing_key.public_key(),'device-1234567890','nonce-1234567890')['device_token']
    for status in ['BLOQUEADA','CANCELADA','EXPIRADA']:
        svc.update(lic['id'],{'status':status})
        with pytest.raises(LicenseError): svc.validate(token,'device-1234567890','nonce-1234567890')
    svc.renew(lic['id'],90)
    assert svc.get(lic['id'])['status']=='ATIVA'
    assert svc.validate(token,'device-1234567890','nonce-1234567890')

def test_expiry_uses_server_clock(svc):
    lic=svc.create('PRO',30,1)
    svc.activate(lic['code'],'device-1234567890','nonce-1234567890')
    svc.update(lic['id'],{'expires_at':1})
    with pytest.raises(LicenseError,match='expirada'): svc.activate(lic['code'],'device-1234567890','nonce-1234567890')

def test_permanent_and_release(svc):
    lic=svc.create('GRATIS',0,1)
    svc.activate(lic['code'],'device-1234567890','nonce-1234567890')
    assert svc.get(lic['id'])['expires_at'] is None
    svc.release(lic['id'],'device-1234567890')
    svc.activate(lic['code'],'device-2234567890','nonce-1234567890')
    assert svc.get(lic['id'])['activation_count']==1

def test_concurrent_device_limit(svc):
    lic=svc.create('PRO',30,1)
    def activate(n):
        try: svc.activate(lic['code'],f'device-12345678{n:02}','nonce-1234567890');return True
        except LicenseError: return False
    with ThreadPoolExecutor(max_workers=6) as pool: results=list(pool.map(activate,range(6)))
    assert sum(results)==1

def test_api_admin_protection_and_lifecycle(svc):
    app=create_app(svc,'admin',password_hash('a-long-owner-password'), 'https://licenses.example.com')
    c=TestClient(app,base_url='https://licenses.example.com')
    assert c.get('/admin/licenses').status_code==401
    auth=('admin','a-long-owner-password')
    assert c.get('/admin',auth=auth).status_code==200
    r=c.post('/admin/licenses',auth=auth,json={'plan':'PRO','days':30,'device_limit':1})
    assert r.status_code==200
    lic=r.json()
    assert c.post('/admin/licenses',auth=auth,headers={'Origin':'https://evil.example'},json={'plan':'PRO','days':30,'device_limit':1}).status_code==403
    response=c.post('/v1/activate',json={'code':lic['code'],'device_id':'device-1234567890','nonce':'nonce-1234567890'})
    assert response.status_code==200
    assert 'code' not in c.get('/admin/licenses',auth=auth).json()[0]
    assert c.post('/v1/activate',json={'code':'invalid','device_id':'device-1234567890','nonce':'nonce-1234567890'}).status_code in (400,422)
    assert c.patch('/admin/licenses/'+lic['id'],auth=auth,json={'device_limit':0}).status_code==422

def test_trusted_proxy_separates_client_rate_limits(svc):
    from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
    app=create_app(svc,'admin',password_hash('a-long-owner-password'),'https://licenses.example.com')
    wrapped=ProxyHeadersMiddleware(app,trusted_hosts=['172.30.83.2'])
    c=TestClient(wrapped,client=('172.30.83.2',1234))
    for _ in range(120):assert c.get('/health',headers={'X-Forwarded-For':'203.0.113.5'}).status_code==200
    assert c.get('/health',headers={'X-Forwarded-For':'203.0.113.5'}).status_code==429
    assert c.get('/health',headers={'X-Forwarded-For':'203.0.113.6'}).status_code==200


def test_delete_revokes_code_tokens_and_preserves_other_license(svc):
    lic=svc.create('PRO',30,1);other=svc.create('EMPRESA',0,1)
    response=svc.activate(lic['code'],'device-1234567890','nonce-1234567890')
    token=verify_envelope(response,svc.signing_key.public_key(),'device-1234567890','nonce-1234567890')['device_token']
    svc.delete(lic['id'])
    assert [x['id'] for x in svc.list()]==[other['id']]
    with pytest.raises(LicenseError):svc.activate(lic['code'],'device-1234567890','nonce-1234567890')
    with pytest.raises(LicenseError):svc.validate(token,'device-1234567890','nonce-1234567890')
    with pytest.raises(LicenseError):svc.renew(lic['id'],30)
    with svc.db() as db:
        assert db.execute('SELECT COUNT(*) FROM devices WHERE license_id=?',(lic['id'],)).fetchone()[0]==0
        assert db.execute("SELECT COUNT(*) FROM audit WHERE license_id=? AND action='delete'",(lic['id'],)).fetchone()[0]==1


def test_delete_api_requires_owner_origin_and_matching_confirmation(svc):
    c=TestClient(create_app(svc,'admin',password_hash('a-long-owner-password'),'https://licenses.example.com'),base_url='https://licenses.example.com')
    lic=svc.create('PRO',30,1);path='/admin/licenses/'+lic['id'];auth=('admin','a-long-owner-password')
    assert c.request('DELETE',path,json={'confirmation':lic['id']}).status_code==401
    assert c.request('DELETE',path,auth=auth,json={'confirmation':'wrong'}).status_code==422
    assert c.request('DELETE',path,auth=auth,json={'confirmation':lic['id']},headers={'Origin':'https://evil.example'}).status_code==403
    assert svc.get(lic['id'])['status']=='ATIVA'
    assert c.request('DELETE',path,auth=auth,json={'confirmation':lic['id']}).json()=={'deleted':True}
    assert c.request('DELETE',path,auth=auth,json={'confirmation':lic['id']}).status_code==400
