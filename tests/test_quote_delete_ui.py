import os
import tkinter as tk
from tkinter import ttk
import pytest
from orcaprime.ui import App
from orcaprime.storage import Store
from test_business import create_quote
from test_workshop_ui import click, descendants

pytestmark=pytest.mark.skipif(os.name!='nt' and not os.environ.get('DISPLAY'),reason='Requires display')

@pytest.mark.parametrize('delivered',[False,True])
def test_delete_quote_button_confirms_and_refreshes_list(tmp_path,monkeypatch,delivered):
    root=tk.Tk();answer=[False];prompts=[]
    def confirm(*args,**kwargs):prompts.append(args[1]);return answer[0]
    monkeypatch.setattr('tkinter.messagebox.askyesno',confirm)
    try:
        s=Store(tmp_path/'db');qid=create_quote(s);q=s.get_quote(qid)
        if delivered:s.set_service_status([qid],'ENTREGUE')
        app=App(root,s,auto_start=False);app.show_main();app.navigate('quotes');root.update()
        root.state('normal');root.geometry('920x650');app.quote_tabs.select(1 if delivered else 0);root.update()
        tree=app.quote_trees[delivered];tree.selection_set(str(qid))
        button=next(x for x in descendants(app.body) if isinstance(x,ttk.Button) and x.cget('text')=='Excluir orçamento')
        assert button.winfo_ismapped() and button.winfo_height()>=button.winfo_reqheight()
        button.invoke();assert s.get_quote(qid)
        assert q['number'] in prompts[-1] and q['customer']['name'] in prompts[-1]
        answer[0]=True;button.invoke();root.update()
        assert not s.list_quotes() and not tree.get_children()
    finally:root.destroy()
