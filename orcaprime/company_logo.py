"""A compact embedded company logo, independent of the original local file."""
import base64
import io
import warnings
from pathlib import Path
from PIL import Image, ImageOps, UnidentifiedImageError


def normalize_logo(path):
    source=Path(path)
    if source.stat().st_size>10*1024*1024:raise ValueError('Escolha uma logo de até 10 MB.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            with Image.open(source) as image:
                if image.width*image.height>20000000:raise ValueError('A imagem é grande demais. Use uma logo menor.')
                image=ImageOps.exif_transpose(image).convert('RGBA')
                image.thumbnail((800,400),Image.Resampling.LANCZOS)
                output=io.BytesIO();image.save(output,format='PNG',optimize=True)
    except (UnidentifiedImageError,OSError,Image.DecompressionBombError,Image.DecompressionBombWarning) as exc:
        raise ValueError('Selecione uma imagem PNG, JPG ou WebP válida.') from exc
    return base64.b64encode(output.getvalue()).decode('ascii')


def logo_bytes(encoded):
    try:
        if not isinstance(encoded,str) or len(encoded)>2000000:raise ValueError()
        raw=base64.b64decode(encoded,validate=True)
        with Image.open(io.BytesIO(raw)) as image:
            if image.format!='PNG' or image.width>800 or image.height>400:raise ValueError()
            image.verify()
        return raw
    except Exception as exc:
        raise ValueError('Logo da empresa inválida. Cadastre a imagem novamente.') from exc


class CompanyLogo:
    def company_logo(self):
        with self.connect() as db:row=db.execute("SELECT value FROM meta WHERE key='company_logo'").fetchone()
        return row[0] if row else ''

    def save_company_logo(self,path):
        encoded=normalize_logo(path) if path is not None else ''
        with self.connect() as db:
            if encoded:db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('company_logo',?)",(encoded,))
            else:db.execute("DELETE FROM meta WHERE key='company_logo'")


def logo_flowable(encoded,width=160,height=60):
    from reportlab.platypus import Image as PDFImage
    raw=logo_bytes(encoded)
    with Image.open(io.BytesIO(raw)) as image:w,h=image.size
    scale=min(width/w,height/h)
    result=PDFImage(io.BytesIO(raw),width=w*scale,height=h*scale,mask='auto');result.hAlign='LEFT'
    return result
