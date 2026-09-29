import os
import statistics
import time
import tkinter as tk
from tkinter import ttk
import pytest
from orcaprime.widgets import styles, table

pytestmark=pytest.mark.skipif(os.name!='nt' and not os.environ.get('DISPLAY'),reason='Requires display')

def test_table_redraw_is_faster_than_tiny_tiled_row():
    root=tk.Tk()
    try:
        styles(root);root.geometry('1280x650')
        tree=table(root,[('client','Cliente',400),('service','Serviço',750)])
        for n in range(100):tree.insert('','end',values=(f'Cliente {n}','Manutenção'))
        root.update();style=ttk.Style(root);current=style.layout('Treeview.Row')
        def redraw():
            samples=[]
            for _ in range(4):
                start=time.perf_counter();tree.yview_scroll(1,'units');root.update();samples.append(time.perf_counter()-start)
            return statistics.median(samples)
        optimized=redraw()
        legacy=tk.PhotoImage(master=root,width=2,height=2)
        legacy.put('#04152e',to=(0,0,2,1));legacy.put('#294b70',to=(0,1,2,2))
        style.element_create('Legacy.row','image',legacy,border=(0,0,0,1),sticky='nsew')
        style.layout('Treeview.Row',[('Legacy.row',{'sticky':'nsew'})]);root.update()
        previous=redraw();style.layout('Treeview.Row',current)
        print(f' redraw optimized={optimized:.4f}s previous={previous:.4f}s',flush=True)
        assert optimized < previous*.6
        assert optimized < .25
    finally:root.destroy()
