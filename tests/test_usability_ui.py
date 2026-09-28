import os
import time
import threading
import tkinter as tk
from tkinter import ttk
import pytest
from orcaprime.storage import Store
from orcaprime.widgets import Form
from test_workshop_ui import Harness, descendants, click

pytestmark=pytest.mark.skipif(os.name!='nt' and not os.environ.get('DISPLAY'),reason='Requires display')

def pump(root,predicate,seconds=3):
    end=time.monotonic()+seconds
    while not predicate() and time.monotonic()<end:
        root.update();time.sleep(.01)
    assert predicate()

def test_customer_form_footer_visible_and_saves_at_small_height(tmp_path):
    root=tk.Tk();store=Store(tmp_path/'db')
    try:
        form=Form(root,'Novo cliente',[(k,k,None) for k in ('name','document','phone','email','address')],{},store.save_customer,lambda:None)
        form.geometry('550x380');root.update()
        save=next(w for w in descendants(form) if isinstance(w,ttk.Button) and w.cget('text')=='Salvar')
        assert save.winfo_rooty()+save.winfo_height()<=form.winfo_rooty()+form.winfo_height()
        form.vars['name'].set('Cliente novo');save.invoke()
        assert store.list_customers()[0]['name']=='Cliente novo'
    finally:root.destroy()

def test_empty_customer_list_can_create_customer_inside_new_os(tmp_path):
    root=tk.Tk();store=Store(tmp_path/'db')
    try:
        app=Harness(root,store);app.edit_order();root.update()
        win=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
        click(win,'+ Novo cliente');root.update()
        form=next(w for w in win.winfo_children() if isinstance(w,Form))
        form.vars['name'].set('Cliente na OS');click(form,'Salvar');root.update()
        assert win.order_fields['customer_id'].get().endswith('Cliente na OS')
        win.order_fields['equipment'].set('Notebook');click(win,'Salvar dados')
        assert app.workshop.list_orders()[0]['customer']['name']=='Cliente na OS'
        win.geometry('700x460');root.update()
        save=next(w for w in descendants(win) if isinstance(w,ttk.Button) and w.cget('text')=='Salvar dados')
        assert save.winfo_rooty()+save.winfo_height()<=win.winfo_rooty()+win.winfo_height()
    finally:root.destroy()

def test_background_work_does_not_block_tk_and_destroy_is_safe():
    from orcaprime.windowing import background
    root=tk.Tk();frame=ttk.Frame(root);frame.pack();release=threading.Event();done=[];pulse=[];errors=[]
    root.report_callback_exception=lambda *args:errors.append(args)
    try:
        background(frame,lambda:release.wait(2),lambda result,error:done.append(result))
        root.after(10,lambda:pulse.append(True));pump(root,lambda:bool(pulse))
        assert not done
        frame.destroy();release.set();root.update()
        assert not errors
    finally:release.set();root.destroy()

def test_main_opens_maximized_on_windows(tmp_path):
    if os.name!='nt':pytest.skip('Windows window state')
    from orcaprime.ui import App
    root=tk.Tk()
    try:
        App(root,Store(tmp_path/'db'),auto_start=False);root.update()
        assert root.state()=='zoomed'
    finally:root.destroy()

def test_add_photos_saves_new_order_and_shows_preview(tmp_path,monkeypatch):
    from PIL import Image
    path=tmp_path/'celular.png';Image.new('RGB',(800,600),'blue').save(path)
    monkeypatch.setattr('tkinter.filedialog.askopenfilenames',lambda **kwargs:(str(path),))
    root=tk.Tk();errors=[];root.report_callback_exception=lambda *args:errors.append(args)
    try:
        store=Store(tmp_path/'db');store.save_customer({'name':'Cliente'})
        app=Harness(root,store);app.edit_order();root.update()
        win=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
        win.order_fields['equipment'].set('Celular')
        click(win,'Adicionar fotos')
        def preview_ready():return any(getattr(w,'image',None) is not None for w in descendants(win))
        pump(root,preview_ready)
        order=app.workshop.list_orders()[0]
        assert order['attachments'][0]['filename']=='celular.jpg'
        assert not errors
    finally:root.destroy()

def test_technician_cannot_use_inline_customer_creation(tmp_path):
    root=tk.Tk()
    try:
        store=Store(tmp_path/'db');app=Harness(root,store);app.actor={'role':'TECNICO'}
        app.edit_order();root.update()
        button=next(w for w in descendants(root) if isinstance(w,ttk.Button) and w.cget('text')=='+ Novo cliente')
        assert button.instate(['disabled'])
        button.invoke();assert store.list_customers()==[]
    finally:root.destroy()

def test_cannot_close_application_during_photo_import(tmp_path,monkeypatch):
    from orcaprime.ui import App
    notices=[];monkeypatch.setattr('tkinter.messagebox.showinfo',lambda *args,**kwargs:notices.append(args))
    root=tk.Tk()
    try:
        app=App(root,Store(tmp_path/'db'),auto_start=False)
        win=tk.Toplevel(root);win._busy_import=True
        app.close();assert not app.closed
        app.forget_login();assert not app.closed
        assert len(notices)==2
    finally:root.destroy()

def test_customer_registration_continues_to_device_intake_with_photos(tmp_path,monkeypatch):
    from PIL import Image
    from orcaprime.ui import App
    path=tmp_path/'entrada.png';Image.new('RGB',(640,480),'blue').save(path)
    monkeypatch.setattr('tkinter.filedialog.askopenfilenames',lambda **kwargs:(str(path),))
    root=tk.Tk();errors=[];root.report_callback_exception=lambda *args:errors.append(args)
    try:
        store=Store(tmp_path/'db');app=App(root,store,auto_start=False);app.show_main();app.navigate('customers')
        app.edit_record(True);root.update()
        form=next(w for w in root.winfo_children() if isinstance(w,Form))
        form.vars['name'].set('Cliente com aparelho');form.vars['whatsapp'].set('64999999999');form.vars['city'].set('Rio Verde')
        click(form,'Salvar e registrar aparelho/fotos');root.update()
        win=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
        cid=store.list_customers()[0]['id']
        assert win.order_fields['customer_id'].get().startswith(str(cid)+' — ')
        win.order_fields['equipment'].set('Celular');win.order_fields['checklist'].set('Tela trincada no canto direito; sem carregador.')
        click(win,'Adicionar fotos')
        pump(root,lambda:any(getattr(w,'image',None) is not None for w in descendants(win)))
        order=app.workshop.list_orders()[0]
        assert order['customer_id']==cid
        assert order['customer']['whatsapp']=='64999999999'
        assert order['checklist']=='Tela trincada no canto direito; sem carregador.'
        assert order['attachments'][0]['filename']=='entrada.jpg'
        assert not errors
    finally:root.destroy()
