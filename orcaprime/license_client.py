import base64
import json
import re
import secrets
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse
import requests
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from .vault import protect, unprotect

ALPHABET='ABCDEFGHJKLMNPQRSTUVWXYZ23456789'

def format_code(text):
    raw=''.join(c for c in text.upper() if c in ALPHABET)[:20]
    return '-'.join(raw[i:i+4] for i in range(0,len(raw),4))

def mask_code(text):
    raw=text.replace('-','')
    return raw[:2]+'**-****-****-****-**'+raw[-2:] if len(raw)==20 else ''

def verify_envelope(envelope,public_key,device,nonce):
    try:
        raw=base64.b64decode(envelope['payload'],validate=True)
        signature=base64.b64decode(envelope['signature'],validate=True)
        public_key.verify(signature,raw)
        p=json.loads(raw)
        if p['device_id']!=device or p['nonce']!=nonce or p['status']!='ATIVA': raise ValueError()
        if not 0<p['lease_seconds']<=900: raise ValueError()
        if p['expires_at'] is not None and p['expires_at']<=p['issued_at']: raise ValueError()
        if p['plan'] not in ('GRATIS','PRO','EMPRESA') or not p['license_id']: raise ValueError()
        return p
    except (KeyError,ValueError,TypeError,InvalidSignature):
        raise ValueError('Resposta de licenciamento inválida ou adulterada.') from None

class LicenseFailure(ValueError):
    def __init__(self,message,network=False): super().__init__(message);self.network=network

class LicenseClient:
    def __init__(self,config,data_dir):
        url=config.get('license_url','').rstrip('/')
        parsed=urlparse(url)
        if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.query or parsed.fragment:
            raise ValueError('O endereço HTTPS do servidor de licenças não foi configurado no build.')
        try: self.public_key=Ed25519PublicKey.from_public_bytes(base64.b64decode(config['public_key'],validate=True))
        except (KeyError,ValueError): raise ValueError('A chave pública de licenciamento não foi configurada no build.') from None
        self.url=url;self.dir=Path(data_dir);self.dir.mkdir(parents=True,exist_ok=True)
        identity=self.dir/'device-id.txt'
        if not identity.exists(): identity.write_text(str(uuid.uuid4()),encoding='utf-8')
        self.device=identity.read_text(encoding='utf-8').strip()
        self.token=None;self.payload=None;self.deadline=0
        path=self.dir/'activation.dat'
        if path.exists():
            try: self.token=unprotect(path.read_bytes()).decode()
            except Exception: self.token=None
    def request(self,endpoint,body):
        nonce=secrets.token_urlsafe(24);body=dict(body,nonce=nonce,device_id=self.device)
        started=time.monotonic()
        try:
            response=requests.post(self.url+endpoint,json=body,timeout=(5,12),allow_redirects=False)
        except requests.RequestException:
            raise LicenseFailure('Falha de conexão com o servidor de licenciamento. Verifique sua internet.',True) from None
        if response.status_code==429:
            raise LicenseFailure('Servidor ocupado. A validação será tentada novamente.',True)
        if response.status_code>=500:
            raise LicenseFailure('Servidor de licenciamento indisponível. Tente novamente.',True)
        if response.status_code!=200:
            messages={'invalid':'Licença inválida.','blocked':'Licença bloqueada.','expired':'Licença expirada.',
                      'cancelled':'Licença cancelada.','limit':'Limite de dispositivos atingido.'}
            try: code=response.json().get('code')
            except ValueError: code=None
            self.deadline=0
            raise LicenseFailure(messages.get(code,'Não foi possível validar a licença. Confira o código e tente novamente.'))
        try: payload=verify_envelope(response.json(),self.public_key,self.device,nonce)
        except ValueError as e: self.deadline=0;raise LicenseFailure(str(e)) from None
        self.payload=payload;self.deadline=started+payload['lease_seconds']
        return payload
    def activate(self,code):
        code=format_code(code)
        if len(code)!=24: raise LicenseFailure('Informe os cinco blocos de quatro caracteres.')
        p=self.request('/v1/activate',{'code':code})
        token=p.get('device_token')
        if not isinstance(token,str) or not token: self.deadline=0;raise LicenseFailure('Resposta de ativação incompleta.')
        path=self.dir/'activation.dat';temp=path.with_suffix('.tmp')
        temp.write_bytes(protect(token.encode()));temp.replace(path)
        self.token=token
        return p
    def validate(self):
        if not self.token: raise LicenseFailure('Ative o OrçaPrime para continuar.')
        return self.request('/v1/validate',{'token':self.token})
    def allowed(self): return bool(self.payload) and time.monotonic()<self.deadline
