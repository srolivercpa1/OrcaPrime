"""DPAPI vincula o token ao usuário do Windows. Outros SOs são apenas desenvolvimento."""
import ctypes
import os
from ctypes import wintypes

class Blob(ctypes.Structure):
    _fields_=[('size',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_ubyte))]

def _dpapi(data,decrypt=False):
    buffer=ctypes.create_string_buffer(data)
    source=Blob(len(data),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_ubyte)));target=Blob()
    crypt=ctypes.windll.crypt32
    if decrypt:
        ok=crypt.CryptUnprotectData(ctypes.byref(source),None,None,None,None,1,ctypes.byref(target))
    else:
        ok=crypt.CryptProtectData(ctypes.byref(source),'OrçaPrime',None,None,None,1,ctypes.byref(target))
    if not ok: raise OSError('Não foi possível proteger a ativação no Windows.')
    try: return ctypes.string_at(target.data,target.size)
    finally:
        ctypes.windll.kernel32.LocalFree.argtypes=[ctypes.c_void_p]
        ctypes.windll.kernel32.LocalFree(target.data)

def protect(data):
    if os.name=='nt': return b'DP1'+_dpapi(data)
    return b'DEV'+data

def unprotect(data):
    if data.startswith(b'DP1') and os.name=='nt': return _dpapi(data[3:],True)
    if data.startswith(b'DEV') and os.name!='nt': return data[3:]
    raise ValueError('Ativação pertence a outro ambiente ou usuário.')
