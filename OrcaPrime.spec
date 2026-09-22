# Executar exclusivamente no Windows para gerar OrcaPrime.exe.
from pathlib import Path
import json
import base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
root = Path(SPECPATH)
config = root / 'config' / 'client.json'
if not config.exists():
    raise SystemExit('Execute scripts/configure_client.py com URL e chave pública reais antes do build.')
values=json.loads(config.read_text(encoding='utf-8'))
if not values['license_url'].startswith('https://'):
    raise SystemExit('HTTPS obrigatório.')
Ed25519PublicKey.from_public_bytes(base64.b64decode(values['public_key'], validate=True))
a = Analysis([str(root/'run_app.py')], pathex=[str(root)],
    binaries=[], datas=[(str(config),'config'),(str(root/'assets'/'orcaprime.ico'),'assets')],
    hiddenimports=[], hookspath=[], runtime_hooks=[],
    excludes=['licensing','pytest','fastapi','uvicorn','httpx'], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='OrcaPrime',
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
    console=False, icon=str(root/'assets'/'orcaprime.ico'))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='OrcaPrime')
