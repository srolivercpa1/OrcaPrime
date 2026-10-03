import hashlib
import hmac
import secrets
from sqlalchemy import select
from .db import database,User


def hash_password(password):
    salt=secrets.token_bytes(16)
    result=hashlib.scrypt(password.encode(),salt=salt,n=16384,r=8,p=1)
    return salt.hex()+':'+result.hex()

def verify_password(password,encoded):
    try:
        salt,expected=encoded.split(':')
        return hmac.compare_digest(hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex(),expected)
    except (ValueError,TypeError): return False

def digest(token): return hashlib.sha256(token.encode()).hexdigest()

def create_owner(db,email,password):
    """A fixed primary key makes simultaneous first-owner claims mutually exclusive."""
    email=email.strip().lower();password=password.strip()
    if not 12<=len(password)<=200: raise ValueError('A senha precisa ter de 12 a 200 caracteres.')
    if len(email)>254 or len(email)<3 or email.count('@')!=1 or any(c.isspace() for c in email):
        raise ValueError('Informe um e-mail válido.')
    local,domain=email.split('@')
    if not local or '.' not in domain or domain.startswith('.') or domain.endswith('.'):
        raise ValueError('Informe um e-mail válido.')
    if db.scalar(select(User).where(User.role=='OWNER')): raise ValueError('Proprietário já configurado.')
    owner=User(id='00000000000000000000000000000001',email=email,name='Sketch Inc',password=hash_password(password),role='OWNER')
    db.add(owner);db.flush()
    return owner

def bootstrap(url,email,password):
    engine,factory=database(url)
    try:
        with factory.begin() as db: create_owner(db,email,password)
    finally: engine.dispose()
