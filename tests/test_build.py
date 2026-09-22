import base64
from pathlib import Path
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from scripts.configure_client import configure

def test_build_rejects_missing_or_example_configuration(tmp_path):
    for url,key in [('', ''),('http://server.com',''),('https://licencas.seudominio.com.br','')]:
        with pytest.raises(ValueError):configure(url,key,tmp_path/'client.json')

def test_build_accepts_only_valid_public_key(tmp_path):
    with pytest.raises(ValueError):configure('https://licencas.empresa.com','not-valid',tmp_path/'client.json')
    key=base64.b64encode(Ed25519PrivateKey.generate().public_key().public_bytes_raw()).decode()
    configure('https://licencas.empresa.com',key,tmp_path/'client.json')
    assert (tmp_path/'client.json').exists()
