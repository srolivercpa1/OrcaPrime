import os
import tkinter as tk
from tkinter import ttk
import pytest

@pytest.mark.skipif(os.name != 'nt' and not os.environ.get('DISPLAY'), reason='Requires display')
def test_scroll_over_children_is_scoped_and_cleans_up():
    from orcaprime.workshop_ui import scroll_frame
    root = tk.Tk()
    root.geometry('400x240')
    try:
        left = ttk.Frame(root); left.pack(side='left', fill='both', expand=True)
        right = ttk.Frame(root); right.pack(side='left', fill='both', expand=True)
        first = scroll_frame(left); second = scroll_frame(right)
        for frame in (first, second):
            for i in range(50): ttk.Label(frame, text=f'Campo {i}').pack()
        root.update()
        canvas = first.master; other = second.master
        first.winfo_children()[0].event_generate('<MouseWheel>', delta=-120)
        root.update()
        assert canvas.yview()[0] > 0
        assert other.yview()[0] == 0
        first.winfo_children()[0].event_generate('<MouseWheel>', delta=120)
        root.update()
        assert canvas.yview()[0] == 0
        left.destroy(); root.update()
        second.winfo_children()[0].event_generate('<MouseWheel>', delta=-120)
        root.update()
        assert other.yview()[0] > 0
    finally:
        root.destroy()
