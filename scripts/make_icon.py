"""Package the user-supplied brand artwork as Windows multi-size icons."""
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[1]
source = root / 'assets' / 'brand.png'
with Image.open(source) as original:
    image = original.convert('RGBA')
    image.save(root/'assets'/'orcaprime.ico', sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
    image.save(root/'assets'/'orcaprime.png')
