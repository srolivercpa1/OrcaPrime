import os
import tkinter as tk
from tkinter import ttk
import pytest
from orcaprime.storage import Store
from test_workshop_ui import Harness, descendants, click

pytestmark=pytest.mark.skipif(os.name!='nt' and not os.environ.get('DISPLAY'),reason='Requires display')

def test_categories_filter_search_and_rename(tmp_path):
    root=tk.Tk();errors=[];root.report_callback_exception=lambda *args:errors.append(args)
    try:
        app=Harness(root,Store(tmp_path/'db'))
        battery=app.workshop.save_part({'description':'Bateria iPhone','sku':'B01'})
        screen=app.workshop.save_part({'description':'Tela Samsung','sku':'T01'})
        app.navigate('stock');root.update()
        widgets=list(descendants(app.body));box=next(w for w in widgets if isinstance(w,ttk.Combobox))
        search=next(w for w in widgets if isinstance(w,ttk.Entry) and not isinstance(w,ttk.Combobox))
        tree=next(w for w in widgets if isinstance(w,ttk.Treeview))
        assert tuple(box.cget('values'))==('Todas as categorias','Bateria','Tela')
        box.set('Bateria');box.event_generate('<<ComboboxSelected>>');root.update()
        assert tree.get_children()==(str(battery),)
        search.insert(0,'Samsung');root.update();assert not tree.get_children()
        search.delete(0,'end');root.update();tree.selection_set(str(battery));click(root,'Editar');root.update()
        win=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
        entry=next(w for w in descendants(win) if isinstance(w,ttk.Entry) and not isinstance(w,ttk.Combobox))
        entry.delete(0,'end');entry.insert(0,'Cabo USB');click(win,'Salvar');root.update()
        assert box.get()=='Cabo' and tree.get_children()==(str(battery),)
        assert 'Bateria' not in box.cget('values') and 'Cabo' in box.cget('values')
        box.set('Todas as categorias');box.event_generate('<<ComboboxSelected>>');root.update()
        assert len(tree.get_children())==2 and not errors
    finally:root.destroy()
