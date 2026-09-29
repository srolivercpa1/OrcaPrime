import os
import tkinter as tk
from tkinter import ttk
import pytest
from orcaprime.widgets import styles, table

pytestmark=pytest.mark.skipif(os.name!='nt' and not os.environ.get('DISPLAY'),reason='Requires display')

@pytest.mark.parametrize('scaling',[1.0,1.5,2.0])
def test_table_headers_align_with_values_and_rows_have_visible_rules(scaling):
    from PIL import ImageGrab
    root=tk.Tk()
    try:
        root.tk.call('tk','scaling',scaling);styles(root);root.geometry('700x400+40+40')
        tree=table(root,[('client','Cliente',240),('service','Procedimento',260)])
        for i in range(12):tree.insert('','end',iid=str(i),values=(f'Cliente {i}',f'Serviço {i}'))
        root.update()
        for col in ('client','service'):
            assert str(tree.heading(col,'anchor'))==str(tree.column(col,'anchor'))=='w'
        def check_rule():
            root.update();shot=ImageGrab.grab();pixels=shot.load()
            visible=[tree.bbox(row) for row in tree.get_children() if tree.bbox(row)]
            x,y,w,h=visible[1]
            px=tree.winfo_rootx()+w-20;py=tree.winfo_rooty()+y
            background=pixels[px,py+h//2][:3]
            border=[pixels[px,py+h+offset][:3] for offset in (-2,-1,0)]
            assert any(color!=background for color in border), 'Falta linha separadora entre registros'
        root.update();shot=ImageGrab.grab();pixels=shot.load()
        x,y,w,h=tree.bbox('0','client');ox=tree.winfo_rootx();oy=tree.winfo_rooty()
        def first_text_x(top,bottom,color):
            return min(px for px in range(ox+x+1,ox+x+w-2)
                       for py in range(oy+top,oy+bottom)
                       if pixels[px,py][:3]==color)
        assert abs(first_text_x(2,y-2,(163,189,223))-first_text_x(y+2,y+h-2,(238,245,255)))<=3
        check_rule();tree.yview_scroll(2,'units');root.geometry('580x340+40+40');check_rule()
        tree.selection_set('3');root.update();assert tree.selection()==('3',)
        assert tree.item('3','values')==('Cliente 3','Serviço 3')
    finally:root.destroy()
