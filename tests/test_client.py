import base64
import time
from unittest.mock import patch
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from orcaprime.license_client import LicenseClient, LicenseFailure
from licensing.service import LicenseService

@pytest.fixture
def client_service(tmp_path):
    key=Ed25519PrivateKey.generate();svc=LicenseService(tmp_path/'license.db',key,b'p'*32)
    conf={'license_url':'https://licenses.example.com','public_key':base64.b64encode(key.public_key().public_bytes_raw()).decode()}
    return LicenseClient(conf,tmp_path/'client'),svc,conf

class Response:
    status_code=200
    def __init__(self,data): self.data=data
    def json(self): return self.data

def test_client_activation_persists_token_not_code(client_service,tmp_path):
    client,svc,conf=client_service;lic=svc.create('PRO',30,1)
    def post(url,json,**kwargs): return Response(svc.activate(json['code'],json['device_id'],json['nonce']))
    with patch('orcaprime.license_client.requests.post',side_effect=post): client.activate(lic['code'])
    assert client.allowed()
    assert lic['code'].encode() not in (tmp_path/'client'/'activation.dat').read_bytes()
    restored=LicenseClient(conf,tmp_path/'client')
    assert not restored.allowed()
    assert restored.token==client.token
    client.deadline=time.monotonic()-1
    assert not client.allowed()

def test_invalid_response_revokes_existing_lease(client_service):
    client,svc,conf=client_service
    client.deadline=time.monotonic()+900;client.payload={'plan':'PRO'}
    with patch('orcaprime.license_client.requests.post',return_value=Response({'payload':'bad'})):
        with pytest.raises(LicenseFailure): client.request('/v1/validate',{'token':'x'*48})
    assert not client.allowed()

def test_insecure_endpoint_rejected(tmp_path):
    with pytest.raises(ValueError): LicenseClient({'license_url':'http://example.com'},tmp_path)

def test_gui_smoke(tmp_path):
    import os
    if os.name!='nt' and not os.environ.get('DISPLAY'): pytest.skip('Display virtual ausente; executar no CI Windows.')
    import tkinter as tk
    from orcaprime.ui import App
    from orcaprime.storage import Store
    class ActiveLicense:
        payload={'plan':'PRO','mask':'AB**-****-****-****-**23','expires_at':None}
        def allowed(self): return True
    root=tk.Tk();app=App(root,Store(tmp_path/'app.db'),ActiveLicense(),auto_start=False)
    app.show_main()
    for page in ('dashboard','customers','catalog','quotes','company','backup','license'):
        app.navigate(page);root.update()
    root.destroy()

def test_rate_limit_keeps_existing_lease(client_service):
    client,svc,_=client_service
    client.deadline=time.monotonic()+100;client.payload={'plan':'PRO'}
    response=Response({});response.status_code=429
    with patch('orcaprime.license_client.requests.post',return_value=response):
        with pytest.raises(LicenseFailure) as caught:client.request('/v1/validate',{'token':'x'*48})
    assert caught.value.network
    assert client.allowed()

def test_poll_survives_failed_callback(tmp_path):
    from orcaprime.ui import App
    import queue
    class Root:
        def __init__(self):self.scheduled=[];self.errors=[]
        def after(self,*args):self.scheduled.append(args)
        def report_callback_exception(self,*args):self.errors.append(args)
    app=App.__new__(App);app.root=Root();app.closed=False;app.events=queue.Queue()
    def broken(*args):raise RuntimeError('stale widget')
    app.events.put((broken,None,None));app.poll()
    assert app.root.scheduled
    assert len(app.root.errors)==1


def test_license_lock_preserves_open_editor(tmp_path):
    import os,tkinter as tk
    if os.name!='nt' and not os.environ.get('DISPLAY'):pytest.skip('Display virtual ausente')
    from orcaprime.ui import App
    from orcaprime.storage import Store
    class ActiveLicense:
        payload={'plan':'PRO','mask':'AB**-****-****-****-**23','expires_at':None};token=None
        def allowed(self):return True
    root=tk.Tk();app=App(root,Store(tmp_path/'app.db'),ActiveLicense(),auto_start=False)
    app.show_main();dialog=tk.Toplevel(root);field=tk.Entry(dialog);field.pack();field.insert(0,'Rascunho importante');root.update()
    app.show_activation('Valide para continuar.');root.update()
    assert dialog.winfo_exists()
    assert dialog.state()=='withdrawn'
    app.show_main();root.update()
    assert field.get()=='Rascunho importante'
    assert dialog.state()=='normal'
    root.destroy()

def test_quote_editor_save_controls_fit_window(tmp_path):
    import os,tkinter as tk
    from tkinter import ttk
    if os.name!='nt' and not os.environ.get('DISPLAY'):pytest.skip('Display virtual ausente')
    from orcaprime.quote_editor import QuoteEditor
    from orcaprime.storage import Store
    s=Store(tmp_path/'app.db');s.save_customer({'name':'Cliente teste'})
    from orcaprime.widgets import styles
    root=tk.Tk();styles(root);editor=QuoteEditor(root,s,lambda:None,lambda:None);editor.geometry('820x650');root.update()
    def walk(parent):
        for child in parent.winfo_children():yield child;yield from walk(child)
    save=next(w for w in walk(editor) if isinstance(w,ttk.Button) and w.cget('text')=='Salvar orçamento')
    assert save.winfo_ismapped()
    assert save.winfo_rooty()+save.winfo_height()<=editor.winfo_rooty()+editor.winfo_height()
    root.destroy()
