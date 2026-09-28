import os
import tkinter as tk
from tkinter import ttk
import pytest
from orcaprime.storage import Store
from test_business import create_quote
from test_workshop_ui import descendants, click

pytestmark=pytest.mark.skipif(os.name!='nt' and not os.environ.get('DISPLAY'),reason='Requires display')

@pytest.mark.parametrize('scaling',[1.0,1.5,2.0])
def test_quote_actions_visible_and_delivery_archive(tmp_path,monkeypatch,scaling):
    from orcaprime.ui import App
    root=tk.Tk();errors=[];root.report_callback_exception=lambda *args:errors.append(args)
    monkeypatch.setattr('tkinter.simpledialog.askstring',lambda *args,**kwargs:'Retirado pelo cliente')
    monkeypatch.setattr('tkinter.messagebox.askyesno',lambda *args,**kwargs:True)
    try:
        root.tk.call('tk','scaling',scaling)
        store=Store(tmp_path/'db');qid=create_quote(store)
        app=App(root,store,auto_start=False);app.show_main();app.navigate('quotes');root.update()
        root.state('normal');root.geometry('920x650');root.update()
        for label in ['Editar','Duplicar','Exportar PDF','Relatório completo','Aplicar aos marcados']:
            button=next(w for w in descendants(root) if isinstance(w,ttk.Button) and w.cget('text')==label)
            assert button.winfo_ismapped()
            assert button.winfo_height()>=button.winfo_reqheight()
            assert button.winfo_rooty()+button.winfo_height()<=root.winfo_rooty()+root.winfo_height()
        tree=app.quote_trees[False];tree.focus(str(qid));tree.focus_force();root.update();tree.event_generate('<space>');root.update()
        assert tree.set(str(qid),'mark')=='☑'
        box=next(w for w in descendants(root) if isinstance(w,ttk.Combobox) and 'Aparelho: Entregue' in w.cget('values'))
        box.set('Aparelho: Entregue');click(root,'Aplicar aos marcados');root.update()
        assert not tree.get_children()
        app.quote_tabs.select(1);root.update()
        assert app.quote_trees[True].exists(str(qid))
        assert store.get_quote(qid)['delivered_at']
        assert not errors
    finally:root.destroy()

def test_quote_editor_scroll_and_device_report_save(tmp_path):
    from orcaprime.quote_editor import QuoteEditor
    root=tk.Tk()
    try:
        store=Store(tmp_path/'db');qid=create_quote(store)
        editor=QuoteEditor(root,store,lambda:None,lambda:None,store.get_quote(qid))
        editor.geometry('820x450');root.update()
        save=next(w for w in descendants(editor) if isinstance(w,ttk.Button) and w.cget('text')=='Salvar orçamento')
        assert save.winfo_height()>=save.winfo_reqheight()
        assert save.winfo_rooty()+save.winfo_height()<=editor.winfo_rooty()+editor.winfo_height()
        editor.device_fields['equipment'].set('Notebook');editor.device_fields['serial'].set('ABC123')
        editor.texts['service_report'].insert('1.0','Placa reparada e testada')
        save.invoke();q=store.get_quote(qid)
        assert q['equipment']=='Notebook' and q['serial']=='ABC123'
        assert q['service_report']=='Placa reparada e testada'
    finally:root.destroy()
