"""Validate public deployment information before building a commercial EXE."""
import json
from pathlib import Path
from scripts.configure_client import configure
root=Path(__file__).resolve().parents[1]
configuration=json.loads((root/'config/client-public.json').read_text(encoding='utf-8'))
configure(configuration['license_url'],configuration['public_key'],root/'config/client.json')
print('Configuração pública de licenciamento validada.')
