"""Execute no servidor privado: python -m scripts.setup_server"""
import base64
import getpass
import os
import secrets
from pathlib import Path
from urllib.parse import urlparse
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from licensing.security import password_hash
from scripts.configure_client import configure

def main():
    root=Path.cwd()
    if (root/'.env').exists() or (root/'secrets'/'signing.pem').exists():
        raise SystemExit('Configuração existente. Não sobrescrita; siga o manual para rotação de chaves.')
    origin=input('URL HTTPS real do servidor (sem barra final): ').strip().rstrip('/')
    username=input('Usuário administrativo: ').strip()
    if not username or any(c in username for c in '\r\n=#$\'" '):raise SystemExit('Use um usuário simples, sem espaços ou símbolos especiais.')
    password=getpass.getpass('Senha administrativa (mínimo 16 caracteres): ')
    if password!=getpass.getpass('Repita a senha: '):raise SystemExit('Senhas diferentes.')
    hashed=password_hash(password)
    key=Ed25519PrivateKey.generate();public=base64.b64encode(key.public_key().public_bytes_raw()).decode()
    configure(origin,public,root/'config'/'client.json')
    os.umask(0o077);folder=root/'secrets';folder.mkdir(mode=0o700,exist_ok=True)
    path=folder/'signing.pem'
    path.write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
    pepper=base64.b64encode(secrets.token_bytes(48)).decode()
    env=f'ORCAPRIME_ADMIN_USER={username}\nORCAPRIME_ADMIN_HASH={hashed}\nORCAPRIME_PEPPER={pepper}\nORCAPRIME_PRIVATE_KEY_FILE=/run/secrets/signing.pem\nORCAPRIME_DB=/data/licenses.db\nORCAPRIME_PUBLIC_ORIGIN={origin}\n'
    (root/'.env').write_text(env,encoding='utf-8')
    print('Configuração privada criada. Preserve .env e secrets/signing.pem fora do GitHub.')
    print('GitHub Variable ORCAPRIME_LICENSE_URL:',origin)
    print('GitHub Variable ORCAPRIME_PUBLIC_KEY:',public)
    if os.name=='posix' and os.geteuid()==0:
        from scripts.server_permissions import prepare
        prepare(path)
    else:
        print('Antes de iniciar no Linux: sudo python3 scripts/server_permissions.py')
    print('Inicie: docker compose up -d --build')
if __name__=='__main__':main()
