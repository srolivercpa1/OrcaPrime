import base64
import json
import os
from pathlib import Path
from urllib.parse import urlparse
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def configure(url,key,destination):
    parsed=urlparse(url)
    if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.query or parsed.fragment:
        raise ValueError('Configure ORCAPRIME_LICENSE_URL com um endereço HTTPS válido.')
    if parsed.hostname in ('localhost','example.com','licencas.seudominio.com.br') or parsed.hostname.endswith(('.example','.invalid','.local')):
        raise ValueError('Use o endereço real do servidor, não um exemplo.')
    try: Ed25519PublicKey.from_public_bytes(base64.b64decode(key,validate=True))
    except Exception: raise ValueError('Configure ORCAPRIME_PUBLIC_KEY com a chave pública Ed25519 válida.') from None
    path=Path(destination);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps({'license_url':url.rstrip('/'),'public_key':key},indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':
    configure(os.environ.get('ORCAPRIME_LICENSE_URL',''),os.environ.get('ORCAPRIME_PUBLIC_KEY',''),Path(__file__).resolve().parents[1]/'config'/'client.json')
