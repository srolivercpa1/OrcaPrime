import io
import pytest
from PIL import Image
from orcaprime.storage import Store
from orcaprime.workshop import Workshop

def test_photo_is_resized_and_stored_with_order(tmp_path):
    store=Store(tmp_path/'db'); ws=Workshop(store)
    cid=store.save_customer({'name':'Cliente'});oid=ws.save_order({'customer_id':cid,'equipment':'Celular'})
    path=tmp_path/'foto.png';Image.new('RGB',(3000,2400),'blue').save(path)
    aid=ws.add_photo(oid,path)
    filename,content=ws.attachment_bytes(aid)
    with Image.open(io.BytesIO(content)) as photo:
        assert photo.format=='JPEG' and max(photo.size)<=1920
    assert filename=='foto.jpg'
    assert ws.get_order(oid)['attachments'][0]['id']==aid

def test_bad_photo_does_not_create_attachment(tmp_path):
    store=Store(tmp_path/'db');ws=Workshop(store)
    cid=store.save_customer({'name':'Cliente'});oid=ws.save_order({'customer_id':cid,'equipment':'Celular'})
    path=tmp_path/'foto.jpg';path.write_bytes(b'not image')
    with pytest.raises(ValueError):ws.add_photo(oid,path)
    assert ws.get_order(oid)['attachments']==[]
