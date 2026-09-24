import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from pypdf import PdfReader
from reportlab.lib.units import mm


class ServiceDocumentsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'os.pdf'
        self.order = dict(number='000123', customer={'name': 'João <Silva> & Cia'},
                          equipment='Notebook', serial='SN123', total_cents=10000,
                          paid_cents=2500, balance_cents=7500, delivered_at='2026-09-23',
                          warranty_days=30, warranty_terms='Cobertura configurada.', items=[])

    def export(self, **kwargs):
        from orcaprime.service_documents import export_service_document
        return export_service_document(self.order, {'name': 'Assistência São José'}, self.path, **kwargs)

    def test_receipt_preserves_partial_payment_and_escaped_text(self):
        self.assertEqual(self.export(kind='RECIBO'), self.path)
        text = ''.join(p.extract_text() for p in PdfReader(self.path).pages)
        for expected in ['João <Silva> & Cia', 'NÃO É DOCUMENTO FISCAL', '25,00', '75,00', 'Valor pago', 'Saldo pendente']:
            self.assertIn(expected, text)
        self.assertNotIn('quitado', text.lower())

    def test_warranty_uses_delivery_and_marks_missing(self):
        self.export(kind='GARANTIA')
        text = PdfReader(self.path).pages[0].extract_text()
        self.assertIn('23/10/2026', text)
        self.order['delivered_at'] = ''
        self.export(kind='GARANTIA')
        self.assertIn('Entrega não registrada', PdfReader(self.path).pages[0].extract_text())

    def test_long_thermal_documents_paginate_without_losing_text(self):
        self.order['complaint'] = 'Descrição técnica acentuada & <teste>. ' * 500 + 'FIM DO RELATO'
        for paper, width in [('58mm', 58), ('80mm', 80), ('A4', 210)]:
            self.export(paper=paper)
            reader = PdfReader(self.path)
            self.assertGreater(len(reader.pages), 1)
            self.assertAlmostEqual(float(reader.pages[0].mediabox.width), width * mm, places=2)
            self.assertIn('FIM DO RELATO', ' '.join(''.join(p.extract_text() for p in reader.pages).split()))
            self.assertTrue(all('000123' in p.extract_text() for p in reader.pages))

    def test_label_dimensions_and_invalid_options(self):
        self.export(kind='ETIQUETA')
        page = PdfReader(self.path).pages[0]
        self.assertAlmostEqual(float(page.mediabox.height), 40 * mm, places=2)
        self.assertAlmostEqual(float(page.mediabox.width), 80 * mm, places=2)
        self.assertIn('SN123', page.extract_text())
        for kwargs in [{'paper': 'bad'}, {'kind': 'bad'}]:
            with self.assertRaises(ValueError): self.export(**kwargs)

    def test_printing_rejects_missing_files_and_unavailable_platform(self):
        from orcaprime.service_documents import print_document, open_document, list_printers
        for operation in [open_document, lambda p: print_document(p, 'Office')]:
            with self.assertRaises(FileNotFoundError): operation(self.path)
        self.export()
        with patch('orcaprime.service_documents.sys.platform', 'linux'):
            self.assertEqual(list_printers(), [])
            with self.assertRaisesRegex(RuntimeError, 'Windows'): print_document(self.path, 'Office')

    def test_open_passes_literal_path_without_shell(self):
        from orcaprime.service_documents import open_document
        self.export()
        with patch('orcaprime.service_documents.sys.platform', 'linux'), patch('orcaprime.service_documents.subprocess.Popen') as popen:
            open_document(self.path)
            self.assertEqual(popen.call_args.args[0], ['xdg-open', str(self.path)])

    def test_windows_printto_uses_selected_printer_and_reports_handler_failure(self):
        from orcaprime.service_documents import print_document
        from unittest.mock import MagicMock
        self.export()
        windll = MagicMock()
        windll.shell32.ShellExecuteW.return_value = 31
        with patch('orcaprime.service_documents.sys.platform', 'win32'), patch('orcaprime.service_documents.list_printers', return_value=['Office']), patch('orcaprime.service_documents.ctypes.windll', windll, create=True):
            with self.assertRaisesRegex(RuntimeError, 'leitor PDF'): print_document(self.path, 'Office')
            self.assertEqual(windll.shell32.ShellExecuteW.call_args.args[1:4], ('printto', str(self.path), '"Office"'))
            with self.assertRaises(ValueError): print_document(self.path, 'Office" bad')

    def test_invalid_pdf_cannot_be_opened(self):
        from orcaprime.service_documents import open_document
        self.path.write_text('not a PDF')
        with self.assertRaises(ValueError): open_document(self.path)


def test_service_pdf_embeds_font_for_consistent_printing(tmp_path):
    from orcaprime.service_documents import export_service_document
    path=tmp_path/'font.pdf'
    export_service_document({'number':'1','customer':{'name':'João da Conceição'},'equipment':'Celular'}, {'name':'Assistência'},path)
    fonts=PdfReader(path).pages[0]['/Resources']['/Font'].get_object()
    embedded=[f.get_object().get('/FontDescriptor') for f in fonts.values()]
    assert any(d and '/FontFile2' in d.get_object() for d in embedded)
