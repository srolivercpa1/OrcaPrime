import base64
import os
import secrets
import threading
import time
from collections import OrderedDict, deque
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field, ConfigDict
from cryptography.hazmat.primitives import serialization
from .security import verify_password
from .service import LicenseService, LicenseError

class Activation(BaseModel):
    code: str=Field(min_length=24,max_length=24,pattern=r'^[A-HJ-NP-Z2-9]{4}(?:-[A-HJ-NP-Z2-9]{4}){4}$')
    device_id: str=Field(min_length=16,max_length=64,pattern=r'^[a-zA-Z0-9_-]+$')
    nonce: str=Field(min_length=16,max_length=100,pattern=r'^[a-zA-Z0-9_-]+$')
class Validation(BaseModel):
    token: str=Field(min_length=32,max_length=128)
    device_id: str=Field(min_length=16,max_length=64,pattern=r'^[a-zA-Z0-9_-]+$')
    nonce: str=Field(min_length=16,max_length=100,pattern=r'^[a-zA-Z0-9_-]+$')
class NewLicense(BaseModel):
    plan: Literal['GRATIS','PRO','EMPRESA']='PRO'
    days: Literal[0,30,90,365]=30
    device_limit: int=Field(default=1,ge=1,le=1000)
class UpdateLicense(BaseModel):
    model_config=ConfigDict(extra='forbid')
    plan: Literal['GRATIS','PRO','EMPRESA']|None=None
    status: Literal['ATIVA','BLOQUEADA','EXPIRADA','CANCELADA']|None=None
    expires_at: int|None=Field(default=None,ge=1)
    device_limit: int|None=Field(default=None,ge=1,le=1000)
class Renewal(BaseModel):
    days: Literal[0,30,90,365]


def create_app(service,admin_user,admin_hash,public_origin):
    app=FastAPI(title='OrçaPrime Licenciamento',docs_url=None,redoc_url=None,openapi_url=None)
    auth=HTTPBasic();buckets=OrderedDict();lock=threading.Lock()
    def owner(credentials:HTTPBasicCredentials=Depends(auth)):
        user_ok=secrets.compare_digest(credentials.username.encode(),admin_user.encode())
        pass_ok=verify_password(credentials.password,admin_hash)
        if not (user_ok and pass_ok): raise HTTPException(401,'Acesso não autorizado.',headers={'WWW-Authenticate':'Basic realm="OrcaPrime"'})
        return admin_user
    @app.middleware('http')
    async def protection(request,call_next):
        now=time.monotonic();ip=request.client.host if request.client else 'unknown'
        key=(ip,'admin' if request.url.path.startswith('/admin') else 'client')
        with lock:
            while buckets and now-next(iter(buckets.values()))[-1]>60: buckets.popitem(last=False)
            if key not in buckets and len(buckets)>=10000: return JSONResponse({'detail':'Servidor ocupado.'},503)
            history=buckets.setdefault(key,deque())
            while history and now-history[0]>60: history.popleft()
            if len(history)>=120: return JSONResponse({'detail':'Muitas solicitações. Tente novamente em um minuto.'},429,headers={'Retry-After':'60'})
            history.append(now);buckets.move_to_end(key)
        length=request.headers.get('content-length','0')
        if not length.isdigit() or int(length)>16384: return JSONResponse({'detail':'Solicitação muito grande.'},413)
        if request.method not in ('GET','HEAD','OPTIONS'):
            origin=request.headers.get('origin')
            if origin and origin!=public_origin.rstrip('/'): return JSONResponse({'detail':'Origem não permitida.'},403)
            if request.headers.get('sec-fetch-site')=='cross-site': return JSONResponse({'detail':'Origem não permitida.'},403)
        response=await call_next(request)
        response.headers.update({'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer',
            'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"})
        return response
    @app.exception_handler(LicenseError)
    async def license_error(request,error): return JSONResponse({'code':error.code,'detail':str(error)},400)
    @app.exception_handler(ValueError)
    async def value_error(request,error): return JSONResponse({'detail':str(error)},422)
    @app.exception_handler(RequestValidationError)
    async def validation_error(request,error): return JSONResponse({'detail':'Dados inválidos. Confira os campos e os limites permitidos.'},422)
    @app.get('/health')
    def health(): return {'status':'ok'}
    @app.post('/v1/activate')
    def activate(data:Activation): return service.activate(data.code,data.device_id,data.nonce)
    @app.post('/v1/validate')
    def validate(data:Validation): return service.validate(data.token,data.device_id,data.nonce)
    @app.get('/admin',dependencies=[Depends(owner)])
    def panel(): return FileResponse(Path(__file__).with_name('admin.html'))
    @app.get('/admin/app.js',dependencies=[Depends(owner)])
    def javascript(): return FileResponse(Path(__file__).with_name('admin.js'),media_type='application/javascript')
    @app.get('/admin/style.css',dependencies=[Depends(owner)])
    def css(): return FileResponse(Path(__file__).with_name('admin.css'),media_type='text/css')
    @app.get('/admin/client-config',dependencies=[Depends(owner)])
    def client_config():
        return {'license_url': public_origin.rstrip('/'),
                'public_key': base64.b64encode(service.signing_key.public_key().public_bytes_raw()).decode()}
    @app.get('/admin/licenses',dependencies=[Depends(owner)])
    def licenses(q:str=''): return service.list(q[:200])
    @app.post('/admin/licenses',dependencies=[Depends(owner)])
    def create(data:NewLicense): return service.create(data.plan,data.days,data.device_limit)
    @app.get('/admin/licenses/{id_}',dependencies=[Depends(owner)])
    def get(id_:str): return service.get(id_)
    @app.patch('/admin/licenses/{id_}',dependencies=[Depends(owner)])
    def update(id_:str,data:UpdateLicense): return service.update(id_,data.model_dump(exclude_unset=True))
    @app.post('/admin/licenses/{id_}/renew',dependencies=[Depends(owner)])
    def renew(id_:str,data:Renewal): return service.renew(id_,data.days)
    @app.delete('/admin/licenses/{id_}/devices/{device}',dependencies=[Depends(owner)])
    def release(id_:str,device:str): return service.release(id_,device)
    return app


def from_env():
    required=['ORCAPRIME_PRIVATE_KEY_FILE','ORCAPRIME_PEPPER','ORCAPRIME_ADMIN_USER','ORCAPRIME_ADMIN_HASH','ORCAPRIME_PUBLIC_ORIGIN']
    if any(not os.environ.get(k) for k in required): raise RuntimeError('Configure todas as variáveis do servidor conforme .env.example.')
    origin=os.environ['ORCAPRIME_PUBLIC_ORIGIN'].rstrip('/')
    if not origin.startswith('https://'): raise RuntimeError('Use um domínio HTTPS para o servidor.')
    key=serialization.load_pem_private_key(Path(os.environ['ORCAPRIME_PRIVATE_KEY_FILE']).read_bytes(),password=None)
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    if not isinstance(key,Ed25519PrivateKey): raise RuntimeError('Chave Ed25519 obrigatória.')
    service=LicenseService(os.environ.get('ORCAPRIME_DB','/data/licenses.db'),key,base64.b64decode(os.environ['ORCAPRIME_PEPPER'],validate=True))
    return create_app(service,os.environ['ORCAPRIME_ADMIN_USER'],os.environ['ORCAPRIME_ADMIN_HASH'],origin)
