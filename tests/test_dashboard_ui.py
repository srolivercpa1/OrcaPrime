import os
import tkinter as tk
import pytest
from orcaprime.storage import Store
from orcaprime.workshop import Workshop
from orcaprime.ui import App
from orcaprime.workshop_queries import OrderFilters
from orcaprime.dashboard_ui import DashboardPages

pytestmark=pytest.mark.skipif(os.name!='nt' and not os.environ.get('DISPLAY'),reason='Requires display')

@pytest.mark.parametrize('scaling',[1.0,1.5])
def test_dashboard_navigation_and_card_bounds(tmp_path,scaling):
    root=tk.Tk()
    try:
        root.tk.call('tk','scaling',scaling)
        store=Store(tmp_path/'data.db');cid=store.save_customer({'name':'José'})
        w=Workshop(store);oid=w.save_order({'customer_id':cid,'equipment':'Notebook','due_date':'2020-01-01'})
        app=App(root,store,auto_start=False);app.show_main();root.geometry('920x650');root.update()
        assert app.current_page=='dashboard'
        assert app.dashboard_values['overdue']==1
        for button in app.dashboard_cards.values():
            assert button.winfo_width()>100
            assert button.winfo_rootx()+button.winfo_width()<=root.winfo_rootx()+root.winfo_width()
        app.dashboard_cards['overdue'].invoke();root.update()
        assert app.current_page=='orders'
        assert app.order_filters.deadline=='overdue'
    finally:root.destroy()


def test_technician_starts_in_orders_without_finance_access(tmp_path):
    root=tk.Tk()
    try:
        app=App(root,Store(tmp_path/'db'),auto_start=False,actor={'role':'TECNICO','id':0,'name':'Técnico'})
        app.show_main();root.update()
        assert app.current_page=='orders'
        assert 'dashboard' not in app.nav_buttons
        with pytest.raises(ValueError):app.navigate('finance')
    finally:root.destroy()


def test_title_font_remains_readable_on_available_platform(tmp_path):
    from tkinter import font,ttk
    root=tk.Tk()
    try:
        app=App(root,Store(tmp_path/'db'),auto_start=False);app.show_main();root.update()
        configured=ttk.Style(root).lookup('Title.TLabel','font')
        assert font.Font(root,font=configured).actual('size') >= 20
    finally:root.destroy()


def test_operational_card_opens_only_active_orders(tmp_path):
    root=tk.Tk()
    try:
        store=Store(tmp_path/'db');cid=store.save_customer({'name':'Cliente'})
        w=Workshop(store);active=w.save_order({'customer_id':cid,'equipment':'Celular'})
        closed=w.save_order({'customer_id':cid,'equipment':'Notebook'});w.transition(closed,'CANCELADA','Recusado')
        app=App(root,store,auto_start=False);app.show_main();root.update()
        app.dashboard_cards['active'].invoke();root.update()
        assert app.orders_tree.get_children()==(str(active),)
    finally:root.destroy()


def test_title_widget_uses_title_style_not_global_small_font(tmp_path):
    from tkinter import ttk,font
    root=tk.Tk()
    try:
        app=App(root,Store(tmp_path/'db'),auto_start=False);app.show_main();root.update()
        app.navigate('orders');root.update()
        title=next(w for w in app.body.winfo_children() if isinstance(w,ttk.Label) and w.cget('style')=='Title.TLabel')
        effective=title.cget('font') or ttk.Style(root).lookup('Title.TLabel','font')
        assert font.Font(root,font=effective).actual('size')>=20
    finally:root.destroy()


@pytest.mark.parametrize('scaling',[1.5,2.0])
def test_order_actions_visible_at_minimum_size(tmp_path,scaling):
    from tkinter import ttk
    root=tk.Tk()
    try:
        root.tk.call('tk','scaling',scaling)
        app=App(root,Store(tmp_path/'db'),auto_start=False);app.show_main();root.geometry('920x650');app.navigate('orders');root.update()
        def children(w):
            for c in w.winfo_children():
                yield c
                yield from children(c)
        for text in ('Abrir OS selecionada','Imprimir documentos','Limpar filtros'):
            button=next(w for w in children(app.body) if isinstance(w,ttk.Button) and w.cget('text')==text)
            assert button.winfo_ismapped(),text
            assert button.winfo_rooty()+button.winfo_height()<=root.winfo_rooty()+650,text
    finally:root.destroy()
