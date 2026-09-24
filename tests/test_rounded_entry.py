import os
import tkinter as tk
import pytest
from orcaprime.rounded_entry import RoundedEntry

pytestmark = pytest.mark.skipif(os.name != 'nt' and not os.environ.get('DISPLAY'), reason='Requires display')


def test_password_toggle_keeps_value_and_fits_input():
    root = tk.Tk()
    try:
        root.geometry('480x160')
        value = tk.StringVar(value='Senha de teste 123')
        field = RoundedEntry(root, value, password=True)
        field.pack(fill='x', padx=24, pady=24)
        root.update()
        assert field.entry.cget('show') == '•'
        field.toggle_button.invoke()
        assert field.entry.cget('show') == ''
        assert field.toggle_button.cget('text') == 'Ocultar'
        field.toggle_button.invoke()
        assert field.entry.cget('show') == '•'
        assert value.get() == 'Senha de teste 123'
        submissions = []
        root.bind('<Return>', lambda event: submissions.append(True))
        field.toggle_button.focus_force()
        root.update()
        field.toggle_button.event_generate('<Return>')
        root.update()
        assert field.entry.cget('show') == ''
        assert not submissions
        assert field.entry.winfo_x() + field.entry.winfo_width() < field.toggle_button.winfo_x()
        assert field.toggle_button.winfo_x() + field.toggle_button.winfo_width() < field.winfo_width()
    finally:
        root.destroy()
