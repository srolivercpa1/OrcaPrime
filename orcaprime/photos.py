"""Bounded photo import. Original files are never modified."""
import io
from pathlib import Path
from PIL import Image, ImageOps, UnidentifiedImageError


def prepare_photo(path):
    path=Path(path)
    with path.open('rb') as source:content=source.read(25*1024*1024+1)
    if len(content)>25*1024*1024:raise ValueError('Foto excede 25 MB.')
    try:
        with Image.open(io.BytesIO(content)) as original:
            if original.width*original.height>25_000_000:raise ValueError('Foto excede 25 megapixels.')
            if original.format not in ('JPEG','PNG','WEBP','BMP'):raise ValueError('Use uma foto JPG, PNG, WEBP ou BMP.')
            original.thumbnail((1920,1920))
            photo=ImageOps.exif_transpose(original).convert('RGB')
            output=io.BytesIO();photo.save(output,'JPEG',quality=85,optimize=True)
            return path.stem+'.jpg',output.getvalue()
    except (UnidentifiedImageError,OSError,Image.DecompressionBombError) as error:
        raise ValueError('Não foi possível ler a foto. Escolha uma imagem válida.') from error
