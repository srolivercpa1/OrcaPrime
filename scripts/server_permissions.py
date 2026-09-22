"""Ajusta SOMENTE a chave privada para o usuário do container (Linux)."""
import os
from pathlib import Path

def prepare(path):
    path=Path(path)
    if path.is_symlink() or not path.is_file():raise ValueError('Chave ausente ou link simbólico não permitido.')
    os.chown(path,10001,10001)
    os.chmod(path,0o600)

if __name__=='__main__':
    if os.name!='posix' or os.geteuid()!=0:raise SystemExit('Execute sudo python3 scripts/server_permissions.py no servidor Linux.')
    prepare(Path(__file__).resolve().parents[1]/'secrets'/'signing.pem')
    print('Permissão privada ajustada para UID 10001 do container.')
