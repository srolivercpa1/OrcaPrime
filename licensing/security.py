import base64
import hashlib
import hmac
import secrets


def password_hash(password):
    if len(password)<16: raise ValueError('Use uma senha administrativa de pelo menos 16 caracteres.')
    salt=secrets.token_bytes(16)
    derived=hashlib.scrypt(password.encode(),salt=salt,n=16384,r=8,p=1)
    return base64.b64encode(salt+derived).decode()

def verify_password(password,stored):
    try:
        raw=base64.b64decode(stored,validate=True)
        if len(raw)!=80: return False
        return hmac.compare_digest(hashlib.scrypt(password.encode(),salt=raw[:16],n=16384,r=8,p=1),raw[16:])
    except (ValueError,TypeError): return False
