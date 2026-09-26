import base64
import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

ALPHABET='ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
PLANS=('GRATIS','PRO','EMPRESA')
STATES=('ATIVA','BLOQUEADA','EXPIRADA','CANCELADA')
MESSAGES={'invalid':'Licença inválida.','blocked':'Licença bloqueada.','expired':'Licença expirada.','cancelled':'Licença cancelada.','limit':'Limite de dispositivos atingido.'}

class LicenseError(ValueError):
    def __init__(self,code):
        self.code=code
        super().__init__(MESSAGES.get(code,'Ativação inválida.'))

class LicenseService:
    def __init__(self,path,signing_key,pepper):
        if len(pepper)<32: raise ValueError('O segredo HMAC deve conter pelo menos 32 bytes.')
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        self.signing_key=signing_key;self.pepper=pepper
        with self.db() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS licenses(id TEXT PRIMARY KEY, code_hash TEXT UNIQUE NOT NULL,
            mask TEXT NOT NULL, plan TEXT NOT NULL, status TEXT NOT NULL, created_at INTEGER NOT NULL,
            activated_at INTEGER, expires_at INTEGER, days INTEGER NOT NULL, device_limit INTEGER NOT NULL,
            last_validated_at INTEGER);
            CREATE TABLE IF NOT EXISTS devices(license_id TEXT NOT NULL REFERENCES licenses(id),
            device_id TEXT NOT NULL, token_hash TEXT UNIQUE NOT NULL, activated_at INTEGER NOT NULL,
            last_validated_at INTEGER NOT NULL, PRIMARY KEY(license_id,device_id));
            CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, at INTEGER, action TEXT, license_id TEXT);
            ''')
    @contextmanager
    def db(self):
        db=sqlite3.connect(self.path,timeout=30,isolation_level=None);db.row_factory=sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            db.execute('BEGIN IMMEDIATE');yield db;db.commit()
        except Exception: db.rollback();raise
        finally: db.close()
    def digest(self,text): return hmac.new(self.pepper,text.encode(),hashlib.sha256).hexdigest()
    def audit(self,db,action,id_): db.execute('INSERT INTO audit(at,action,license_id) VALUES(?,?,?)',(int(time.time()),action,id_))
    def create(self,plan,days,device_limit):
        if plan not in PLANS or days not in (0,30,90,365) or not 1<=device_limit<=1000: raise ValueError('Plano, período ou limite inválido.')
        raw=''.join(secrets.choice(ALPHABET) for _ in range(20));code='-'.join(raw[i:i+4] for i in range(0,20,4))
        id_=str(uuid.uuid4());mask=raw[:2]+'**-****-****-****-**'+raw[-2:]
        with self.db() as db:
            db.execute('INSERT INTO licenses VALUES(?,?,?,?,?,?,?,?,?,?,?)',(id_,self.digest(code),mask,plan,'ATIVA',int(time.time()),None,None,days,device_limit,None))
            self.audit(db,'create',id_)
        return dict(self.get(id_),code=code)
    def _public(self,db,row):
        data=dict(row);data.pop('code_hash');data['activation_count']=db.execute('SELECT COUNT(*) FROM devices WHERE license_id=?',(data['id'],)).fetchone()[0]
        if data['status']=='ATIVA' and data['expires_at'] is not None and data['expires_at']<=time.time(): data['status']='EXPIRADA'
        return data
    def get(self,id_):
        with self.db() as db:
            row=db.execute('SELECT * FROM licenses WHERE id=?',(id_,)).fetchone()
            if not row: raise LicenseError('invalid')
            data=self._public(db,row)
            data['devices']=[dict(x) for x in db.execute('SELECT device_id,activated_at,last_validated_at FROM devices WHERE license_id=?',(id_,))]
            return data
    def list(self,search=''):
        with self.db() as db:
            values=[self._public(db,row) for row in db.execute('SELECT * FROM licenses ORDER BY created_at DESC')]
        term=search.strip().upper()
        return [x for x in values if term in (x['id']+' '+x['mask']+' '+x['plan']+' '+x['status']).upper()]
    def _check(self,row,now):
        if not row: raise LicenseError('invalid')
        state={'BLOQUEADA':'blocked','CANCELADA':'cancelled','EXPIRADA':'expired'}.get(row['status'])
        if state: raise LicenseError(state)
        if row['expires_at'] is not None and row['expires_at']<=now: raise LicenseError('expired')
    def _signed(self,row,device,nonce,now,token=None):
        payload={'license_id':row['id'],'mask':row['mask'],'plan':row['plan'],'status':'ATIVA',
                 'device_id':device,'nonce':nonce,'issued_at':now,'expires_at':row['expires_at'],
                 'lease_seconds':min(900,max(0,row['expires_at']-now)) if row['expires_at'] is not None else 900}
        if token: payload['device_token']=token
        raw=json.dumps(payload,separators=(',',':'),sort_keys=True).encode()
        return {'payload':base64.b64encode(raw).decode(),'signature':base64.b64encode(self.signing_key.sign(raw)).decode()}
    def activate(self,code,device,nonce):
        if not re.fullmatch(r'[A-HJ-NP-Z2-9]{4}(?:-[A-HJ-NP-Z2-9]{4}){4}',code): raise LicenseError('invalid')
        now=int(time.time());token=secrets.token_urlsafe(48)
        with self.db() as db:
            row=db.execute('SELECT * FROM licenses WHERE code_hash=?',(self.digest(code),)).fetchone();self._check(row,now)
            exists=db.execute('SELECT 1 FROM devices WHERE license_id=? AND device_id=?',(row['id'],device)).fetchone()
            count=db.execute('SELECT COUNT(*) FROM devices WHERE license_id=?',(row['id'],)).fetchone()[0]
            if not exists and count>=row['device_limit']: raise LicenseError('limit')
            if not row['activated_at']:
                expires=now+row['days']*86400 if row['days'] else None
                db.execute('UPDATE licenses SET activated_at=?,expires_at=? WHERE id=?',(now,expires,row['id']))
            db.execute('INSERT INTO devices VALUES(?,?,?,?,?) ON CONFLICT(license_id,device_id) DO UPDATE SET token_hash=excluded.token_hash,last_validated_at=excluded.last_validated_at',(row['id'],device,self.digest(token),now,now))
            db.execute('UPDATE licenses SET last_validated_at=? WHERE id=?',(now,row['id']))
            self.audit(db,'activate',row['id'])
            row=db.execute('SELECT * FROM licenses WHERE id=?',(row['id'],)).fetchone()
            return self._signed(row,device,nonce,now,token)
    def validate(self,token,device,nonce):
        now=int(time.time())
        with self.db() as db:
            row=db.execute('SELECT l.* FROM licenses l JOIN devices d ON d.license_id=l.id WHERE d.token_hash=? AND d.device_id=?',(self.digest(token),device)).fetchone();self._check(row,now)
            db.execute('UPDATE devices SET last_validated_at=? WHERE token_hash=?',(now,self.digest(token)))
            db.execute('UPDATE licenses SET last_validated_at=? WHERE id=?',(now,row['id']))
            return self._signed(row,device,nonce,now)
    def update(self,id_,changes):
        allowed={'plan','status','expires_at','device_limit'}
        if not changes or set(changes)-allowed: raise ValueError('Alteração inválida.')
        if 'plan' in changes and changes['plan'] not in PLANS: raise ValueError('Plano inválido.')
        if 'status' in changes and changes['status'] not in STATES: raise ValueError('Situação inválida.')
        if 'device_limit' in changes and not 1<=changes['device_limit']<=1000: raise ValueError('Limite inválido.')
        if changes.get('expires_at') is not None and (not isinstance(changes['expires_at'],int) or changes['expires_at']<1): raise ValueError('Vencimento inválido.')
        with self.db() as db:
            if not db.execute('SELECT 1 FROM licenses WHERE id=?',(id_,)).fetchone(): raise LicenseError('invalid')
            count=db.execute('SELECT COUNT(*) FROM devices WHERE license_id=?',(id_,)).fetchone()[0]
            if changes.get('device_limit',count)<count: raise ValueError('Libere dispositivos antes de reduzir o limite.')
            if 'expires_at' in changes:
                row=db.execute('SELECT activated_at FROM licenses WHERE id=?',(id_,)).fetchone()
                if row['activated_at'] is None: raise ValueError('Defina vencimento após a primeira ativação, ou altere por renovação.')
            db.execute('UPDATE licenses SET '+','.join(k+'=?' for k in changes)+' WHERE id=?',(*changes.values(),id_))
            self.audit(db,'update',id_)
        return self.get(id_)
    def renew(self,id_,days):
        if days not in (0,30,90,365): raise ValueError('Período inválido.')
        now=int(time.time())
        with self.db() as db:
            row=db.execute('SELECT * FROM licenses WHERE id=?',(id_,)).fetchone()
            if not row: raise LicenseError('invalid')
            expiry=(max(now,row['expires_at'] or now)+days*86400) if days and row['activated_at'] else None
            db.execute("UPDATE licenses SET status='ATIVA',days=?,expires_at=? WHERE id=?",(days,expiry,id_));self.audit(db,'renew',id_)
        return self.get(id_)
    def release(self,id_,device):
        with self.db() as db:
            db.execute('DELETE FROM devices WHERE license_id=? AND device_id=?',(id_,device));self.audit(db,'release-device',id_)
        return self.get(id_)

    def delete(self,id_):
        """End a contract atomically; retain audit events, never customer data."""
        with self.db() as db:
            if not db.execute('SELECT 1 FROM licenses WHERE id=?',(id_,)).fetchone():
                raise LicenseError('invalid')
            db.execute('DELETE FROM devices WHERE license_id=?',(id_,))
            db.execute('DELETE FROM licenses WHERE id=?',(id_,))
            self.audit(db,'delete',id_)
