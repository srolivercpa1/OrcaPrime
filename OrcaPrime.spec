# Executar exclusivamente no Windows para gerar OrcaPrime.exe.
from pathlib import Path
import reportlab
font_root = Path(reportlab.__file__).resolve().parent / "fonts"
root = Path(SPECPATH)
a = Analysis([str(root/'run_app.py')], pathex=[str(root)],
    binaries=[], datas=[(str(root/'assets'/'premium-banner.png'),'assets'),(str(root/'assets'/'brand.png'),'assets'),(str(root/'assets'/'orcaprime-premium-r2.ico'),'assets'),
        (str(font_root/'Vera.ttf'),'reportlab/fonts'),
        (str(font_root/'VeraBd.ttf'),'reportlab/fonts'),
        (str(font_root/'bitstream-vera-license.txt'),'reportlab/fonts')],
    hiddenimports=[], hookspath=[], runtime_hooks=[],
    excludes=['licensing','pytest','fastapi','uvicorn','httpx'], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='OrcaPrime',
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
    console=False, icon=str(root/'assets'/'orcaprime-premium-r2.ico'))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='OrcaPrime')
