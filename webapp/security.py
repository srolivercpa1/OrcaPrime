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

def bootstrap(url,email,password):
    if len(password)<12: raise ValueError('A senha precisa ter pelo menos 12 caracteres.')
    engine,factory=database(url)
    with factory.begin() as db:
        if db.scalar(select(User).where(User.role=='OWNER')): raise ValueError('Proprietário já configurado.')
        db.add(User(email=email.strip().lower(),name='Sketch Inc',password=hash_password(password),role='OWNER'))
    engine.dispose()
