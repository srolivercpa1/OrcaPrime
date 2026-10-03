import os
import secrets
import time
import threading
from collections import OrderedDict,deque
from pathlib import Path
from fastapi import FastAPI,Request,Depends,HTTPException
from fastapi.responses import JSONResponse,FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel,Field,ConfigDict
from typing import Literal
from sqlalchemy import select,delete
from sqlalchemy.exc import IntegrityError
from .db import database,User,Company,Session,Audit
from .security import hash_password,verify_password,digest

class Input(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
class Login(Input):
    email:str=Field(min_length=3,max_length=254)
    password:str=Field(min_length=1,max_length=200)
    remember:bool=False
class PasswordChange(Input):
    current:str=Field(min_length=1,max_length=200)
    password:str=Field(min_length=12,max_length=200)
class NewCompany(Input):
    name:str=Field(min_length=2,max_length=160)
    email:str=Field(min_length=3,max_length=254)
    password:str=Field(min_length=12,max_length=200)
    days:int=Field(default=30,ge=1,le=3650)
class CompanyChange(Input):
    active:bool|None=None
    days:int|None=Field(default=None,ge=1,le=3650)
class NewUser(Input):
    name:str=Field(min_length=2,max_length=160)
    email:str=Field(min_length=3,max_length=254)
    password:str=Field(min_length=12,max_length=200)
    role:Literal['ADMIN','ATENDIMENTO','TECNICO','FINANCEIRO']='ATENDIMENTO'
class UserChange(Input):
    role:Literal['ADMIN','ATENDIMENTO','TECNICO','FINANCEIRO']|None=None
    active:bool|None=None
    password:str|None=Field(default=None,min_length=12,max_length=200)

def user_json(u): return {'id':u.id,'name':u.name,'email':u.email,'role':u.role,'active':u.active}
def company_json(c): return {'id':c.id,'name':c.name,'active':c.active,'expires':c.expires,'settings':{k:v for k,v in c.settings.items() if k!='fiscal'}}

def create_app(database_url,secure_cookie=False,public_origin=None,setup_token=None):
    app=FastAPI(title='OrçaPrime Web',version='1.0',docs_url=None,redoc_url=None,openapi_url=None)
    engine,factory=database(database_url)
    app.state.factory=factory
    app.state.engine=engine
    buckets=OrderedDict(); lock=threading.Lock()
    dummy=hash_password(secrets.token_urlsafe(20))
    def db_dep():
        with factory.begin() as db: yield db
    def actor(request:Request,db=Depends(db_dep)):
        token=request.cookies.get('orcaprime_session','')
        session=db.get(Session,digest(token)) if token else None
        if not session or session.expires<int(time.time()): raise HTTPException(401,'Entre na sua conta para continuar.')
        user=db.get(User,session.user_id)
        if not user or not user.active: raise HTTPException(401,'Acesso revogado.')
        if user.company_id:
            # Serialize company mutations (PostgreSQL) including last-admin and stock checks.
            statement=select(Company).where(Company.id==user.company_id)
            if request.method not in ('GET','HEAD'): statement=statement.with_for_update()
            company=db.scalar(statement)
            if request.method not in ('GET','HEAD'):
                # A revocation may have committed while this request waited for the lock.
                db.expire_all()
                session=db.get(Session,digest(token))
                user=db.get(User,session.user_id) if session else None
                if not session or session.expires<int(time.time()) or not user or not user.active:
                    raise HTTPException(401,'Acesso revogado. Entre novamente.')
                company=db.get(Company,user.company_id)
            if not company or not company.active or company.expires<int(time.time()):
                raise HTTPException(403,'Assinatura suspensa ou vencida. Entre em contato com a Sketch Inc.')
        if request.method not in ('GET','HEAD') and not secrets.compare_digest(request.headers.get('X-CSRF-Token',''),session.csrf):
            raise HTTPException(403,'Sessão inválida. Atualize a página.')
        request.state.csrf=session.csrf
        return user
    def require(user,*roles):
        if user.role not in roles: raise HTTPException(403,'Seu perfil não permite esta ação.')
    def audit(db,user,action,target):
        db.add(Audit(company_id=user.company_id,actor=user.id,action=action,target=target))
    @app.middleware('http')
    async def protections(request,call_next):
        if request.method not in ('GET','HEAD','OPTIONS'):
            origin=request.headers.get('origin')
            expected=public_origin or str(request.base_url).rstrip('/')
            if (origin and origin!=expected) or request.headers.get('sec-fetch-site')=='cross-site':
                return JSONResponse({'detail':'Origem não permitida.'},403)
            size=0; chunks=[]
            async for chunk in request.stream():
                size+=len(chunk)
                if size>8*1024*1024: return JSONResponse({'detail':'Arquivo ou solicitação acima de 8 MB.'},413)
                chunks.append(chunk)
            request._body=b''.join(chunks)
        if request.url.path in ('/api/login','/api/setup') and request.method=='POST':
            ip=request.client.host if request.client else 'unknown'; now=time.monotonic()
            with lock:
                while buckets and now-next(iter(buckets.values()))[-1]>900: buckets.popitem(last=False)
                if ip not in buckets and len(buckets)>=10000: return JSONResponse({'detail':'Tente novamente mais tarde.'},429)
                history=buckets.setdefault(ip,deque())
                while history and now-history[0]>900: history.popleft()
                if len(history)>=30: return JSONResponse({'detail':'Muitas tentativas. Aguarde 15 minutos.'},429)
                history.append(now); buckets.move_to_end(ip)
        response=await call_next(request)
        response.headers.update({'X-Content-Type-Options':'nosniff','Referrer-Policy':'same-origin','Cache-Control':'no-store','X-Frame-Options':'DENY','Content-Security-Policy':"default-src 'self'; img-src 'self' blob: data:; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"})
        if secure_cookie: response.headers['Strict-Transport-Security']='max-age=31536000'
        return response
    @app.exception_handler(IntegrityError)
    async def conflict(request,error): return JSONResponse({'detail':'Registro em conflito. Verifique se este e-mail já está cadastrado.'},409)
    @app.exception_handler(RequestValidationError)
    async def invalid_input(request,error):
        # Pydantic's default response includes input values, including passwords/codes.
        return JSONResponse({'detail':'Confira os campos e tente novamente.'},422)
    @app.get('/health')
    def health(): return {'status':'ok','version':'1.0'}
    @app.post('/api/login')
    def login(data:Login,db=Depends(db_dep)):
        u=db.scalar(select(User).where(User.email==data.email.lower()))
        valid=verify_password(data.password,u.password if u else dummy)
        if not u or not valid or not u.active: raise HTTPException(401,'E-mail ou senha inválidos.')
        if u.company_id:
            c=db.get(Company,u.company_id)
            if not c.active or c.expires<int(time.time()): raise HTTPException(403,'Assinatura suspensa ou vencida. Contate a Sketch Inc.')
        token=secrets.token_urlsafe(32); csrf=secrets.token_urlsafe(32); ttl=2592000 if data.remember else 43200
        db.execute(delete(Session).where(Session.expires<int(time.time())))
        db.add(Session(id=digest(token),user_id=u.id,csrf=csrf,expires=int(time.time())+ttl))
        result=JSONResponse({**user_json(u),'csrf':csrf})
        result.set_cookie('orcaprime_session',token,httponly=True,secure=secure_cookie,samesite='strict',max_age=ttl if data.remember else None)
        return result
    @app.get('/api/me')
    def me(request:Request,u=Depends(actor),db=Depends(db_dep)):
        return {**user_json(u),'csrf':request.state.csrf,'company':company_json(db.get(Company,u.company_id)) if u.company_id else None}
    @app.post('/api/logout')
    def logout(request:Request,u=Depends(actor),db=Depends(db_dep)):
        db.execute(delete(Session).where(Session.id==digest(request.cookies['orcaprime_session'])))
        response=JSONResponse({'ok':True});response.delete_cookie('orcaprime_session');return response
    @app.post('/api/password')
    def change_password(data:PasswordChange,u=Depends(actor),db=Depends(db_dep)):
        if not verify_password(data.current,u.password):raise HTTPException(401,'Senha atual incorreta.')
        u.password=hash_password(data.password)
        db.execute(delete(Session).where(Session.user_id==u.id));audit(db,u,'ALTERAR_SENHA',u.id)
        return {'ok':True}
    @app.get('/api/companies')
    def companies(u=Depends(actor),db=Depends(db_dep)):
        require(u,'OWNER');return [company_json(c) for c in db.scalars(select(Company).order_by(Company.name))]
    @app.post('/api/companies')
    def new_company(data:NewCompany,u=Depends(actor),db=Depends(db_dep)):
        require(u,'OWNER')
        c=Company(name=data.name,expires=int(time.time())+data.days*86400);db.add(c);db.flush()
        db.add(User(company_id=c.id,name=data.name,email=data.email.lower(),password=hash_password(data.password),role='ADMIN'))
        audit(db,u,'CRIAR_EMPRESA',c.id);db.flush();return company_json(c)
    @app.patch('/api/companies/{id}')
    def change_company(id:str,data:CompanyChange,u=Depends(actor),db=Depends(db_dep)):
        require(u,'OWNER');c=db.scalar(select(Company).where(Company.id==id).with_for_update())
        if not c: raise HTTPException(404,'Empresa não encontrada.')
        if data.active is not None: c.active=data.active
        if data.days is not None: c.expires=max(c.expires,int(time.time()))+data.days*86400
        if data.active is False:
            db.execute(delete(Session).where(Session.user_id.in_(select(User.id).where(User.company_id==id))))
        audit(db,u,'ALTERAR_ASSINATURA',id);return company_json(c)
    @app.get('/api/users')
    def users(u=Depends(actor),db=Depends(db_dep)):
        require(u,'ADMIN');return [user_json(x) for x in db.scalars(select(User).where(User.company_id==u.company_id))]
    @app.post('/api/users')
    def new_user(data:NewUser,u=Depends(actor),db=Depends(db_dep)):
        require(u,'ADMIN');x=User(company_id=u.company_id,name=data.name,email=data.email.lower(),password=hash_password(data.password),role=data.role)
        db.add(x);db.flush();audit(db,u,'CRIAR_USUARIO',x.id);return user_json(x)
    def target_user(db,u,id):
        require(u,'ADMIN');x=db.scalar(select(User).where(User.id==id,User.company_id==u.company_id))
        if not x: raise HTTPException(404,'Usuário não encontrado.')
        if x.id==u.id: raise HTTPException(409,'Não é possível remover ou alterar seu próprio acesso nesta tela.')
        return x
    def preserve_admin(db,x):
        if x.role=='ADMIN' and x.active:
            admins=list(db.scalars(select(User.id).where(User.company_id==x.company_id,User.role=='ADMIN',User.active==True)))
            if len(admins)<=1:raise HTTPException(409,'Mantenha pelo menos um administrador ativo.')
    @app.patch('/api/users/{id}')
    def edit_user(id:str,data:UserChange,u=Depends(actor),db=Depends(db_dep)):
        x=target_user(db,u,id)
        if data.active is False or (data.role is not None and data.role!='ADMIN'):preserve_admin(db,x)
        for k,v in data.model_dump(exclude_none=True).items(): setattr(x,k,hash_password(v) if k=='password' else v)
        db.execute(delete(Session).where(Session.user_id==x.id));audit(db,u,'ALTERAR_USUARIO',x.id);return user_json(x)
    @app.delete('/api/users/{id}')
    def delete_user(id:str,u=Depends(actor),db=Depends(db_dep)):
        x=target_user(db,u,id);preserve_admin(db,x);db.execute(delete(Session).where(Session.user_id==id));db.delete(x);audit(db,u,'EXCLUIR_USUARIO',id);return {'ok':True}
    from .setup import register as register_setup
    register_setup(app,db_dep,setup_token)
    from .fiscal import register as register_fiscal
    register_fiscal(app,db_dep,actor,require,audit)
    from .operations import register
    register(app,db_dep,actor,require,audit)
    static=Path(__file__).parent/'static'
    @app.get('/')
    def index(): return FileResponse(static/'index.html')
    @app.get('/brand.png')
    def logo(): return FileResponse(Path(__file__).parent.parent/'assets/brand.png')
    app.mount('/static',StaticFiles(directory=static),name='static')
    return app
