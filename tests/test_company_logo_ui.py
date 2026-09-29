import os
import tkinter as tk
from tkinter import ttk
import pytest
from PIL import Image
from orcaprime.storage import Store
from orcaprime.ui import App
from orcaprime.workshop import Workshop
from test_workshop_ui import click, descendants

pytestmark=pytest.mark.skipif(os.name!='nt' and not os.environ.get('DISPLAY'),reason='Requires display')


def test_company_logo_saved_and_reloaded_across_navigation(tmp_path,monkeypatch):
    path=tmp_path/'logo.png';Image.new('RGB',(200,80),'blue').save(path)
    monkeypatch.setattr('tkinter.filedialog.askopenfilename',lambda **kwargs:str(path))
    monkeypatch.setattr('tkinter.messagebox.askyesno',lambda *args,**kwargs:True)
    root=tk.Tk()
    try:
        store=Store(tmp_path/'db');app=App(root,store,auto_start=False);app.show_main();app.navigate('company')
        click(root,'Adicionar / trocar logo');root.update();assert store.company_logo()
        app.navigate('customers');app.navigate('company');root.update()
        assert any(getattr(w,'image',None) is not None for w in descendants(app.body))
        click(root,'Remover logo');assert not store.company_logo()
    finally:root.destroy()


def test_customer_delete_cancel_then_confirm_includes_os(tmp_path,monkeypatch):
    root=tk.Tk();answer=[False];prompts=[]
    def confirm(*args,**kwargs):prompts.append(args[1]);return answer[0]
    monkeypatch.setattr('tkinter.messagebox.askyesno',confirm)
    try:
        store=Store(tmp_path/'db');cid=store.save_customer({'name':'Cliente'})
        w=Workshop(store);oid=w.save_order({'customer_id':cid,'equipment':'Celular'})
        app=App(root,store,auto_start=False);app.show_main();app.navigate('customers');root.update()
        tree=next(x for x in descendants(app.body) if isinstance(x,ttk.Treeview));tree.selection_set(str(cid))
        click(root,'Excluir cliente');assert w.get_order(oid) and store.list_customers()
        answer[0]=True;click(root,'Excluir cliente')
        assert '1 OS' in prompts[-1] and not w.list_orders() and not store.list_customers()
    finally:root.destroy()
