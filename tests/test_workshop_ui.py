import os
import tkinter as tk
from tkinter import ttk
import pytest
from orcaprime.storage import Store
from orcaprime.workshop import Workshop
from orcaprime.workshop_ui import WorkshopPages

pytestmark=pytest.mark.skipif(os.name!='nt' and not os.environ.get('DISPLAY'),reason='Requires display')

def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)

class Harness(WorkshopPages):
    def __init__(self,root,store):
        self.root=root;self.store=store;self.actor={'role':'ADMIN'};self.workshop=Workshop(store);self.body=ttk.Frame(root);self.body.pack(fill='both',expand=True)
    def guard(self):pass
    def safe(self,action):return action
    def navigate(self,page):
        for c in self.body.winfo_children():c.destroy()
        getattr(self,'page_'+page)()

def click(win,label):
    next(w for w in descendants(win) if isinstance(w,ttk.Button) and w.cget('text')==label).invoke()

def test_workshop_pages_and_real_order_save(tmp_path,monkeypatch):
    monkeypatch.setattr('orcaprime.service_documents.list_printers',lambda:[])
    root=tk.Tk();root.geometry('1180x790')
    try:
        store=Store(tmp_path/'work.db');store.save_customer({'name':'Cliente teste'})
        app=Harness(root,store)
        for page in ('orders','stock','finance','warranties','reports','printers','suppliers'):
            app.navigate(page);root.update()
        app.edit_order();root.update();win=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
        entries=[w for w in descendants(win) if isinstance(w,ttk.Entry) and not isinstance(w,ttk.Combobox)]
        entries[0].insert(0,'Notebook de teste')
        click(win,'Salvar dados');root.update();order=app.workshop.list_orders()[0]
        assert order['equipment']=='Notebook de teste' and order['warranty_days']==0
        click(win,'Adicionar peça / serviço');root.update()
        dialog=[w for w in root.winfo_children() if isinstance(w,tk.Toplevel)][-1]
        inputs=[w for w in descendants(dialog) if isinstance(w,ttk.Entry) and not isinstance(w,ttk.Combobox)]
        inputs[0].insert(0,'Diagnóstico');inputs[2].delete(0,'end');inputs[2].insert(0,'10,00');click(dialog,'Salvar')
        assert app.workshop.get_order(order['id'])['total_cents']==1000
        app.workshop.transition(order['id'],'DIAGNOSTICO');app.workshop.transition(order['id'],'AGUARDANDO_APROVACAO');app.workshop.transition(order['id'],'EM_REPARO','Cliente autorizou')
        click(win,'Receber pagamento');root.update();dialog=[w for w in root.winfo_children() if isinstance(w,tk.Toplevel)][-1];click(dialog,'Salvar')
        assert app.workshop.get_order(order['id'])['paid_cents']==1000
        app.navigate('finance');app.navigate('reports');root.update()
    finally:root.destroy()


def test_real_login_and_integrated_pages(tmp_path,monkeypatch):
    from orcaprime.ui import App
    from orcaprime.user_ui import authenticate_window
    from orcaprime.users import Users
    from orcaprime.widgets import styles
    monkeypatch.setattr('orcaprime.service_documents.list_printers',lambda:[])
    root=tk.Tk();root.geometry('1180x790');styles(root)
    store=Store(tmp_path/'app.db')
    errors=[]
    root.report_callback_exception=lambda *args:errors.append(args)
    def fill_setup():
        win=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
        entries=[w for w in descendants(win) if isinstance(w,(tk.Entry,ttk.Entry))]
        for widget,value in zip(entries,['gestor','SenhaSegura123','SenhaSegura123']):widget.insert(0,value)
        click(win,'Criar administrador')
    root.after(100,fill_setup)
    try:
        actor=authenticate_window(root,store)
        assert actor['role']=='ADMIN'
        app=App(root,store,actor=actor)
        for page in app.allowed_pages():
            app.navigate(page);root.update()
        assert not errors
        assert Users(store).authenticate('gestor','SenhaSegura123')['id']==actor['id']
    finally:root.destroy()


def test_combined_order_filters_clear_and_multiline_save(tmp_path):
    from orcaprime.workshop_queries import OrderFilters
    root=tk.Tk()
    try:
        store=Store(tmp_path/'new.db');cid=store.save_customer({'name':'João'})
        app=Harness(root,store)
        first=app.workshop.save_order({'customer_id':cid,'equipment':'Celular','technician':'Ana','priority':'URGENTE','due_date':'2020-01-01'})
        app.workshop.save_order({'customer_id':cid,'equipment':'Notebook','technician':'Bia'})
        app.order_filters=OrderFilters(technician='Ana',priority='URGENTE',deadline='overdue')
        app.navigate('orders');root.update()
        assert app.orders_tree.get_children()==(str(first),)
        click(root,'Limpar filtros');root.update()
        assert len(app.orders_tree.get_children())==2
        app.edit_order(first);root.update()
        win=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
        win.order_fields['complaint'].set('Linha um\nLinha dois')
        click(win,'Salvar dados');root.update()
        assert app.workshop.get_order(first)['complaint']=='Linha um\nLinha dois'
    finally:root.destroy()


def test_label_selection_restricts_paper_and_printer_preferences(tmp_path,monkeypatch):
    monkeypatch.setattr('orcaprime.service_documents.list_printers',lambda:['A4 printer','Label printer'])
    root=tk.Tk()
    try:
        store=Store(tmp_path/'db');cid=store.save_customer({'name':'Cliente'})
        app=Harness(root,store);oid=app.workshop.save_order({'customer_id':cid,'equipment':'Celular'})
        with store.connect() as db:
            db.execute("INSERT INTO meta(key,value) VALUES('printer_settings',?)",('{"A4":"A4 printer","ETIQUETA":"Label printer"}',))
        app.document_dialog(oid);root.update()
        win=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
        combos=[w for w in descendants(win) if isinstance(w,ttk.Combobox)]
        combos[0].set('ETIQUETA');root.update()
        assert tuple(combos[1]['values'])==('ETIQUETA',)
        assert combos[2].get()=='Label printer'
    finally:root.destroy()
