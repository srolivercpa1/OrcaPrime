"""Tenant-scoped workshop operations; every mutation is a single transaction."""
import io
import time
from datetime import date
from typing import Literal
from PIL import Image,ImageOps,UnidentifiedImageError
from fastapi import HTTPException,Depends,UploadFile
from fastapi.responses import Response
from pydantic import Field,ValidationError
from sqlalchemy import select,delete
from .db import Record,Photo,Company,Audit
from .api import Input

class Customer(Input):
    name:str=Field(min_length=2,max_length=160)
    phone:str=Field(default='',max_length=40)
    email:str=Field(default='',max_length=254)
    document:str=Field(default='',max_length=30)
    address:str=Field(default='',max_length=400)
    notes:str=Field(default='',max_length=3000)
class Order(Input):
    customer_id:str=Field(min_length=1,max_length=32)
    device:str=Field(min_length=2,max_length=160)
    brand:str=Field(default='',max_length=80)
    serial:str=Field(default='',max_length=80)
    description:str=Field(default='',max_length=4000)
    accessories:str=Field(default='',max_length=1000)
    technician:str=Field(default='',max_length=100)
    service:str=Field(default='',max_length=4000)
    due:str=Field(default='',max_length=10)
    amount:int=Field(default=0,ge=0,le=100000000)
    status:Literal['AGUARDANDO','EM_ANDAMENTO','PRONTO','ENTREGUE']='AGUARDANDO'
    warranty:int=Field(default=90,ge=0,le=3650)
class Quote(Input):
    customer_id:str=Field(min_length=1,max_length=32)
    device:str=Field(min_length=2,max_length=160)
    description:str=Field(default='',max_length=4000)
    amount:int=Field(default=0,ge=0,le=100000000)
    status:Literal['PENDENTE','APROVADO','RECUSADO']='PENDENTE'
class Part(Input):
    name:str=Field(min_length=2,max_length=160)
    quantity:int=Field(default=0,ge=0,le=1000000)
    price:int=Field(default=0,ge=0,le=100000000)
    category:str=Field(default='',max_length=80)
class Entry(Input):
    name:str=Field(min_length=2,max_length=160)
    direction:Literal['ENTRADA','SAIDA']='ENTRADA'
    amount:int=Field(gt=0,le=100000000)
    due:str=Field(default='',max_length=10)
    paid:bool=False
class Consumption(Input):
    part_id:str=Field(min_length=1,max_length=32)
    quantity:int=Field(gt=0,le=1000000)
    key:str=Field(min_length=1,max_length=80)
class Settings(Input):
    name:str=Field(min_length=2,max_length=160)
    phone:str=Field(default='',max_length=40)
    document:str=Field(default='',max_length=30)
    address:str=Field(default='',max_length=400)
    warranty_text:str=Field(default='',max_length=4000)

MODELS={'customers':Customer,'orders':Order,'quotes':Quote,'parts':Part,'entries':Entry}
READ={'customers':('ADMIN','ATENDIMENTO','TECNICO'),'orders':('ADMIN','ATENDIMENTO','TECNICO'),'quotes':('ADMIN','ATENDIMENTO'),'parts':('ADMIN','ATENDIMENTO','TECNICO'),'entries':('ADMIN','FINANCEIRO')}
WRITE={**READ,'customers':('ADMIN','ATENDIMENTO'),'parts':('ADMIN',),'entries':('ADMIN','FINANCEIRO')}

def record_json(r): return {'id':r.id,'created':r.created,**r.data}
def normalized_image(content):
    try:
        with Image.open(io.BytesIO(content)) as im:
            if im.width*im.height>20000000 or im.format not in ('JPEG','PNG','WEBP'): raise ValueError()
            im=ImageOps.exif_transpose(im);im.thumbnail((1600,1600));out=io.BytesIO();im.convert('RGB').save(out,'JPEG',quality=82)
            return out.getvalue()
    except (UnidentifiedImageError,ValueError,OSError,Image.DecompressionBombError):
        raise HTTPException(422,'Envie uma imagem PNG, JPEG ou WebP válida de até 20 megapixels.')

def register(app,db_dep,actor,require,audit):
    def records(db,u,kind): return list(db.scalars(select(Record).where(Record.company_id==u.company_id,Record.kind==kind).order_by(Record.created.desc(),Record.id)))
    def get(db,u,kind,id):
        r=db.scalar(select(Record).where(Record.id==id,Record.company_id==u.company_id,Record.kind==kind))
        if not r: raise HTTPException(404,'Registro não encontrado.')
        return r
    def access(u,kind,write=False):
        if kind not in MODELS: raise HTTPException(404,'Página não encontrada.')
        require(u,*(WRITE if write else READ)[kind])
    def validate(kind,data):
        try:
            v=MODELS[kind].model_validate(data).model_dump()
            if v.get('due'): date.fromisoformat(v['due'])
            return v
        except (ValidationError,ValueError): raise HTTPException(422,'Confira os campos obrigatórios, valores e datas informados.')
    def history(data,u,text):
        data['history']=[*data.get('history',[]),{'at':int(time.time()),'user':u.name,'action':text}]
    def deletion_info(db,u,id):
        import hashlib,json
        get(db,u,'customers',id)
        orders=[record_json(r) for r in records(db,u,'orders') if r.data['customer_id']==id]
        quotes=[record_json(r) for r in records(db,u,'quotes') if r.data['customer_id']==id]
        content={'orders':orders,'quotes':quotes}
        content['fingerprint']=hashlib.sha256(json.dumps(content,sort_keys=True).encode()).hexdigest()
        return content
    @app.get('/api/customers/{id}/deletion-preview')
    def deletion_preview(id:str,u=Depends(actor),db=Depends(db_dep)):
        require(u,'ADMIN');return deletion_info(db,u,id)
    @app.get('/api/dashboard')
    def dashboard(u=Depends(actor),db=Depends(db_dep)):
        require(u,'ADMIN','ATENDIMENTO','TECNICO','FINANCEIRO')
        orders=records(db,u,'orders');entries=records(db,u,'entries') if u.role in ('ADMIN','FINANCEIRO') else []
        return {'orders':len(orders),'open':sum(r.data['status']!='ENTREGUE' for r in orders),'ready':sum(r.data['status']=='PRONTO' for r in orders),'delivered':sum(r.data['status']=='ENTREGUE' for r in orders),'total':sum(r.data['amount'] for r in orders),'balance':sum(r.data['amount']*(1 if r.data['direction']=='ENTRADA' else -1) for r in entries if r.data['paid']),'receivable':sum(r.data['amount'] for r in entries if not r.data['paid'] and r.data['direction']=='ENTRADA'),'recent':[record_json(r) for r in orders[:6]] if u.role!='FINANCEIRO' else [],'customers':len(records(db,u,'customers'))}
    @app.get('/api/settings')
    def settings(u=Depends(actor),db=Depends(db_dep)):
        require(u,'ADMIN');c=db.get(Company,u.company_id);return {'name':c.name,**c.settings}
    @app.put('/api/settings')
    def save_settings(data:Settings,u=Depends(actor),db=Depends(db_dep)):
        require(u,'ADMIN');c=db.get(Company,u.company_id);c.name=data.name;c.settings={**c.settings,**data.model_dump(exclude={'name'})};audit(db,u,'CONFIGURAR_EMPRESA',c.id);return {'ok':True}
    @app.post('/api/settings/logo')
    async def upload_logo(file:UploadFile,u=Depends(actor),db=Depends(db_dep)):
        import base64
        require(u,'ADMIN');content=await file.read(6*1024*1024+1)
        if len(content)>6*1024*1024: raise HTTPException(413,'A imagem deve ter no máximo 6 MB.')
        c=db.get(Company,u.company_id);c.settings={**c.settings,'logo':base64.b64encode(normalized_image(content)).decode()};return {'ok':True}
    @app.get('/api/audit')
    def audits(u=Depends(actor),db=Depends(db_dep)):
        require(u,'ADMIN','OWNER');q=select(Audit).order_by(Audit.at.desc()).limit(200)
        if u.company_id:q=q.where(Audit.company_id==u.company_id)
        return [{'at':a.at,'action':a.action,'target':a.target,'actor':a.actor} for a in db.scalars(q)]
    @app.post('/api/quotes/{id}/convert')
    def convert(id:str,u=Depends(actor),db=Depends(db_dep)):
        require(u,'ADMIN','ATENDIMENTO');q=get(db,u,'quotes',id)
        if q.data.get('order_id'): return record_json(get(db,u,'orders',q.data['order_id']))
        get(db,u,'customers',q.data['customer_id'])
        data=Order(**{k:q.data[k] for k in ('customer_id','device','description','amount')}).model_dump();history(data,u,'OS criada a partir do orçamento aprovado')
        r=Record(company_id=u.company_id,kind='orders',data=data);db.add(r);db.flush();q.data={**q.data,'status':'APROVADO','order_id':r.id};audit(db,u,'CONVERTER_ORCAMENTO',q.id);return record_json(r)
    @app.post('/api/orders/{id}/consume')
    def consume(id:str,data:Consumption,u=Depends(actor),db=Depends(db_dep)):
        require(u,'ADMIN','TECNICO');o=get(db,u,'orders',id);d=dict(o.data)
        if d['status']=='ENTREGUE':raise HTTPException(409,'OS entregue não pode ser modificada.')
        if any(x['key']==data.key for x in d.get('parts',[])):return record_json(o)
        p=get(db,u,'parts',data.part_id)
        if p.data['quantity']<data.quantity:raise HTTPException(409,'Estoque insuficiente.')
        p.data={**p.data,'quantity':p.data['quantity']-data.quantity}
        d['parts']=[*d.get('parts',[]),{**data.model_dump(),'name':p.data['name'],'price':p.data['price']}];history(d,u,'Peça utilizada: '+p.data['name']);o.data=d;audit(db,u,'CONSUMIR_PECA',id);return record_json(o)
    @app.get('/api/orders/{id}/photos')
    def photos(id:str,u=Depends(actor),db=Depends(db_dep)):
        access(u,'orders');get(db,u,'orders',id)
        return [{'id':p.id,'name':p.name,'url':'/api/photos/'+p.id} for p in db.scalars(select(Photo).where(Photo.company_id==u.company_id,Photo.order_id==id))]
    @app.post('/api/orders/{id}/photos')
    async def upload(id:str,file:UploadFile,u=Depends(actor),db=Depends(db_dep)):
        access(u,'orders',True);get(db,u,'orders',id);content=await file.read(6*1024*1024+1)
        if len(content)>6*1024*1024:raise HTTPException(413,'A imagem deve ter no máximo 6 MB.')
        existing=list(db.scalars(select(Photo.id).where(Photo.company_id==u.company_id,Photo.order_id==id)))
        if len(existing)>=20:raise HTTPException(409,'Limite de 20 fotos por OS.')
        p=Photo(company_id=u.company_id,order_id=id,name=(file.filename or 'Foto')[:160],content=normalized_image(content));db.add(p);db.flush();audit(db,u,'ADICIONAR_FOTO',id);return {'id':p.id,'url':'/api/photos/'+p.id}
    @app.get('/api/photos/{id}')
    def photo(id:str,u=Depends(actor),db=Depends(db_dep)):
        access(u,'orders');p=db.scalar(select(Photo).where(Photo.id==id,Photo.company_id==u.company_id))
        if not p:raise HTTPException(404,'Foto não encontrada.')
        return Response(p.content,media_type='image/jpeg')
    @app.get('/api/orders/{id}/document')
    def document(id:str,type:Literal['os','garantia']='os',u=Depends(actor),db=Depends(db_dep)):
        from .documents import order_pdf
        access(u,'orders');o=get(db,u,'orders',id);c=get(db,u,'customers',o.data['customer_id']);company=db.get(Company,u.company_id)
        return Response(order_pdf(company,record_json(c),record_json(o),type),media_type='application/pdf',headers={'Content-Disposition':f'inline; filename="OrcaPrime-{type}-{id[:8]}.pdf"'})
    @app.get('/api/{kind}')
    def listing(kind:str,u=Depends(actor),db=Depends(db_dep)):
        access(u,kind);return [record_json(r) for r in records(db,u,kind)]
    @app.post('/api/{kind}')
    def create(kind:str,data:dict,u=Depends(actor),db=Depends(db_dep)):
        access(u,kind,True);v=validate(kind,data)
        if kind in ('orders','quotes'):get(db,u,'customers',v['customer_id'])
        if kind=='orders':
            if v['status']!='AGUARDANDO':raise HTTPException(422,'Uma nova OS começa aguardando atendimento.')
            history(v,u,'Entrada do aparelho')
        if kind=='parts' and not v['category']:
            from orcaprime.stock_categories import category_for
            v['category']=category_for(v['name'])
        if kind=='entries' and v['paid']:v['paid_at']=int(time.time())
        r=Record(company_id=u.company_id,kind=kind,data=v);db.add(r);db.flush();audit(db,u,'CRIAR_'+kind.upper(),r.id);return record_json(r)
    @app.patch('/api/{kind}/{id}')
    def change(kind:str,id:str,data:dict,u=Depends(actor),db=Depends(db_dep)):
        access(u,kind,True);r=get(db,u,kind,id)
        if set(data)-set(MODELS[kind].model_fields):raise HTTPException(422,'Campo não permitido.')
        if kind=='quotes' and r.data.get('order_id'):raise HTTPException(409,'Orçamento convertido não pode ser alterado.')
        if kind=='orders' and r.data['status']=='ENTREGUE':raise HTTPException(409,'OS entregue está arquivada e não pode ser alterada.')
        if kind=='entries' and r.data['paid']:raise HTTPException(409,'Lançamento pago é preservado. Registre um lançamento inverso para estorno.')
        v=validate(kind,{**{k:r.data[k] for k in MODELS[kind].model_fields if k in r.data},**data})
        if kind in ('orders','quotes'):get(db,u,'customers',v['customer_id'])
        if kind=='orders':
            old=r.data['status'];new=v['status'];allowed={'AGUARDANDO':('EM_ANDAMENTO',),'EM_ANDAMENTO':('PRONTO',),'PRONTO':('EM_ANDAMENTO','ENTREGUE',)}
            if new!=old and new not in allowed[old]:raise HTTPException(409,'Avance a OS por atendimento, pronto e entregue.')
            v={**r.data,**v};history(v,u,'Atualizado: '+new)
            if new=='ENTREGUE':v['delivered_at']=int(time.time())
        if kind=='entries' and v['paid']:v['paid_at']=int(time.time())
        r.data=v;audit(db,u,'ALTERAR_'+kind.upper(),id);return record_json(r)
    def delete_order(db,u,o):
        # Completed work retains consumed inventory. Unfinished work returns its parts.
        if o.data['status']!='ENTREGUE':
            for item in o.data.get('parts',[]):
                p=db.get(Record,item['part_id'])
                if p and p.company_id==u.company_id:p.data={**p.data,'quantity':p.data['quantity']+item['quantity']}
        db.execute(delete(Photo).where(Photo.order_id==o.id,Photo.company_id==u.company_id));db.delete(o)
    @app.delete('/api/{kind}/{id}')
    def remove(kind:str,id:str,expected:str|None=None,u=Depends(actor),db=Depends(db_dep)):
        access(u,kind);require(u,'ADMIN');r=get(db,u,kind,id)
        if kind=='entries' and r.data['paid']:raise HTTPException(409,'Lançamentos pagos não podem ser apagados. Registre um estorno.')
        if kind=='parts' and any(any(p['part_id']==id for p in o.data.get('parts',[])) for o in records(db,u,'orders')):raise HTTPException(409,'Peça vinculada a uma OS. Preserve seu histórico.')
        if kind=='customers':
            if expected is not None and expected!=deletion_info(db,u,id)['fingerprint']:raise HTTPException(409,'Os atendimentos mudaram. Feche e confira a exclusão novamente.')
            for o in records(db,u,'orders'):
                if o.data['customer_id']==id:delete_order(db,u,o)
            for q in records(db,u,'quotes'):
                if q.data['customer_id']==id:db.delete(q)
        if kind=='orders':
            for q in records(db,u,'quotes'):
                if q.data.get('order_id')==id:q.data={**q.data,'order_id':None}
            delete_order(db,u,r)
        else:db.delete(r)
        audit(db,u,'EXCLUIR_'+kind.upper(),id);return {'ok':True}
