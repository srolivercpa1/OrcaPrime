import os
import tkinter as tk
import pytest
from datetime import date
from orcaprime.storage import Store
from orcaprime.workshop import Workshop
from orcaprime.ui import App

pytestmark=pytest.mark.skipif(os.name!='nt' and not os.environ.get('DISPLAY'),reason='Requires display')

def test_report_period_updates_real_deliveries(tmp_path):
    root=tk.Tk()
    try:
        store=Store(tmp_path/'db');cid=store.save_customer({'name':'Cliente'})
        w=Workshop(store);oid=w.save_order({'customer_id':cid,'equipment':'Celular','technician':'Ana'})
        for status in ('DIAGNOSTICO','AGUARDANDO_APROVACAO','EM_REPARO','EM_TESTES','PRONTA'):w.transition(oid,status,'Aprovado')
        w.save_order({'receiver':'Cliente','final_checklist':'Testado'},oid);w.transition(oid,'ENTREGUE')
        app=App(root,store,auto_start=False);app.show_main();app.navigate('reports');root.update()
        assert app.productivity_tree.item(app.productivity_tree.get_children()[0])['values']==['Ana',1]
        app.report_period['start'].set('2000-01-01');app.report_period['end'].set('2000-01-31')
        app.refresh_productivity();root.update()
        assert app.productivity_tree.get_children()==()
    finally:root.destroy()


@pytest.mark.parametrize('scaling',[1.5,2.0])
def test_report_export_button_visible_at_minimum_size(tmp_path,scaling):
    from tkinter import ttk
    root=tk.Tk()
    try:
        root.tk.call('tk','scaling',scaling)
        app=App(root,Store(tmp_path/'db'),auto_start=False);app.show_main();root.geometry('920x650');app.navigate('reports');root.update()
        def descendants(w):
            for c in w.winfo_children():
                yield c
                yield from descendants(c)
        button=next(w for w in descendants(app.body) if isinstance(w,ttk.Button) and w.cget('text')=='Exportar produtividade CSV')
        assert button.winfo_ismapped()
        assert button.winfo_rooty()+button.winfo_height()<=root.winfo_rooty()+650
    finally:root.destroy()
