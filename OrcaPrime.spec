# Executar exclusivamente no Windows para gerar OrcaPrime.exe.
from pathlib import Path
root = Path(SPECPATH)
a = Analysis([str(root/'run_app.py')], pathex=[str(root)],
    binaries=[], datas=[(str(root/'assets'/'orcaprime.ico'),'assets')],
    hiddenimports=[], hookspath=[], runtime_hooks=[],
    excludes=['licensing','pytest','fastapi','uvicorn','httpx'], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='OrcaPrime',
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
    console=False, icon=str(root/'assets'/'orcaprime.ico'))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='OrcaPrime')
