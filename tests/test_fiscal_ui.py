import os
import tkinter as tk
from tkinter import ttk
import pytest
from test_workshop_ui import Harness, descendants, click
from orcaprime.user_ui import UserPages
from orcaprime.storage import Store

pytestmark = pytest.mark.skipif(os.name != 'nt' and not os.environ.get('DISPLAY'), reason='Requires display')

class FiscalHarness(Harness, UserPages):
    pass

def test_selected_fiscal_pdf_is_sent_to_selected_printer(tmp_path, monkeypatch):
    from reportlab.pdfgen.canvas import Canvas
    path = tmp_path / 'nota.pdf'
    pdf = Canvas(str(path)); pdf.drawString(20, 20, 'Documento de teste'); pdf.save()
    monkeypatch.setattr('orcaprime.service_documents.list_printers', lambda: ['Impressora fiscal'])
    monkeypatch.setattr('tkinter.filedialog.askopenfilename', lambda **kwargs: str(path))
    monkeypatch.setattr('tkinter.messagebox.showinfo', lambda *args, **kwargs: None)
    sent = []
    monkeypatch.setattr('orcaprime.service_documents.print_document', lambda p, printer: sent.append((str(p), printer)))
    root = tk.Tk()
    try:
        app = FiscalHarness(root, Store(tmp_path / 'app.db'))
        app.navigate('fiscal'); root.update()
        click(root, 'Selecionar PDF da nota')
        combo = next(w for w in descendants(root) if isinstance(w, ttk.Combobox))
        combo.set('Impressora fiscal')
        click(root, 'Imprimir nota')
        assert sent == [(str(path.resolve()), 'Impressora fiscal')]
    finally:
        root.destroy()
