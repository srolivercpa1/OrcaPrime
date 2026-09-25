import os
import tkinter as tk
from tkinter import ttk
import pytest
from PIL import Image
from orcaprime.branding import asset_path
from orcaprime.storage import Store
from orcaprime.ui import App
from orcaprime.widgets import INPUT, TEXT

pytestmark=pytest.mark.skipif(os.name!='nt' and not os.environ.get('DISPLAY'),reason='Requires display')


def test_product_shortcut_defaults_to_product_and_dark_fields(tmp_path):
    root=tk.Tk()
    try:
        app=App(root,Store(tmp_path/'db'),auto_start=False);app.show_main()
        app.dashboard_new_record(True);root.update()
        dialog=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
        assert dialog.vars['kind'].get()=='PRODUTO'
        assert ttk.Style(root).lookup('TEntry','fieldbackground')==INPUT
        assert ttk.Style(root).lookup('Treeview','foreground')==TEXT
        with Image.open(asset_path('brand.png')) as logo:
            assert logo.width==logo.height and logo.width>=256
        dialog.destroy()
    finally:root.destroy()


def test_today_action_filters_persisted_deadlines(tmp_path):
    from datetime import date,timedelta
    from orcaprime.workshop_queries import OrderFilters
    root=tk.Tk()
    try:
        store=Store(tmp_path/'db');cid=store.save_customer({'name':'Cliente'})
        app=App(root,store,auto_start=False);app.show_main()
        today=app.workshop.save_order({'customer_id':cid,'equipment':'Celular','due_date':date.today().isoformat()})
        app.workshop.save_order({'customer_id':cid,'equipment':'Notebook','due_date':(date.today()+timedelta(days=1)).isoformat()})
        app.open_orders(OrderFilters(deadline='today',active_only=True));root.update()
        assert app.orders_tree.get_children()==(str(today),)
    finally:root.destroy()
