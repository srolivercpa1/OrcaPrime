"""Service-order PDFs and safe local PDF viewer/printer integration."""
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import date, timedelta
from html import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from .domain import brl

PAPERS = {'A4': A4, '58mm': (58 * mm, 210 * mm), '80mm': (80 * mm, 297 * mm), 'ETIQUETA': (80 * mm, 40 * mm)}
KINDS = {'OS': 'ORDEM DE SERVIÇO', 'ENTRADA': 'COMPROVANTE DE ENTRADA', 'RECIBO': 'RECIBO', 'GARANTIA': 'TERMO DE GARANTIA', 'ETIQUETA': 'ETIQUETA'}


def _text(value):
    if isinstance(value, dict):
        return '\n'.join(f'{k}: {_text(v)}' for k, v in value.items())
    if isinstance(value, (list, tuple)):
        return '\n'.join(_text(v) for v in value)
    if isinstance(value, bool):
        return 'Sim' if value else 'Não'
    return str(value) if value is not None else ''


def _date(value):
    if not value:
        return 'Não informado'
    try:
        return date.fromisoformat(str(value)[:10]).strftime('%d/%m/%Y')
    except ValueError:
        return str(value)


def _fit(value, width, size=9):
    value = ' '.join(_text(value).split())
    if stringWidth(value, 'Helvetica', size) <= width:
        return value
    while value and stringWidth(value + '...', 'Helvetica', size) > width:
        value = value[:-1]
    return value + '...'


def export_service_document(order, company, destination, kind='OS', paper='A4') -> Path:
    """Export an administrative document; no implicit fiscal or warranty terms."""
    if kind not in KINDS:
        raise ValueError('Tipo de documento inválido.')
    if paper not in PAPERS:
        raise ValueError('Papel inválido. Use A4, 58mm, 80mm ou ETIQUETA.')
    path = Path(destination)
    if path.suffix.lower() != '.pdf':
        raise ValueError('Escolha um arquivo com extensão .pdf.')
    customer = order.get('customer') or {}
    number = _text(order.get('number', ''))
    if kind == 'ETIQUETA' or paper == 'ETIQUETA':
        width, height = PAPERS['ETIQUETA']
        c = canvas.Canvas(str(path), pagesize=(width, height))
        c.setTitle('Etiqueta OS ' + number)
        lines = [company.get('name', ''), 'OS ' + number, customer.get('name', ''),
                 ' '.join(filter(None, [_text(order.get(k)) for k in ('equipment', 'brand', 'model')])),
                 'Série: ' + _text(order.get('serial') or 'Não informada')]
        for i, line in enumerate(lines):
            c.setFont('Helvetica-Bold' if i == 1 else 'Helvetica', 9)
            c.drawString(4 * mm, height - 7 * mm - i * 6 * mm, _fit(line, width - 8 * mm, 9))
        c.save()
        return path
    size = PAPERS[paper]
    thermal = paper != 'A4'
    margin = 4 * mm if thermal else 16 * mm
    font_size = 8 if thermal else 10
    style = ParagraphStyle('ServiceBody', fontName='Helvetica', fontSize=font_size,
                           leading=font_size * 1.4, spaceAfter=5, splitLongWords=True)
    heading = ParagraphStyle('ServiceHeading', parent=style, fontName='Helvetica-Bold', spaceBefore=8)
    story = []

    def paragraph(value, bold=False):
        story.append(Paragraph(escape(_text(value)).replace('\n', '<br/>'), heading if bold else style))

    def field(label, value):
        paragraph(label + ': ' + (_text(value) or 'Não informado'))

    paragraph(company.get('name') or 'Assistência técnica', True)
    for key in ('document', 'phone', 'email', 'address'):
        if company.get(key): paragraph(company[key])
    paragraph(KINDS[kind], True)
    field('OS', number)
    field('Entrada', _date(order.get('created_at')))
    field('Status', order.get('status'))
    paragraph('CLIENTE', True)
    for label, key in [('Nome', 'name'), ('Documento', 'document'), ('Telefone', 'phone'), ('Endereço', 'address')]:
        field(label, customer.get(key))
    paragraph('EQUIPAMENTO', True)
    for label, key in [('Equipamento', 'equipment'), ('Marca', 'brand'), ('Modelo', 'model'), ('Série', 'serial')]:
        field(label, order.get(key))
    if kind in ('OS', 'ENTRADA'):
        for label, key in [('Relato do cliente', 'complaint'), ('Acessórios', 'accessories'), ('Checklist de entrada', 'checklist')]:
            field(label, order.get(key))
    if kind == 'OS':
        field('Diagnóstico', order.get('diagnosis'))
        field('Técnico responsável', order.get('technician'))
        field('Previsão', _date(order.get('due_date')))
    if kind in ('OS', 'RECIBO', 'GARANTIA'):
        paragraph('SERVIÇOS E PEÇAS', True)
        for item in order.get('items', []):
            paragraph(item.get('description', ''))
            field('Tipo', item.get('kind'))
            paragraph(f"Qtd.: {_text(item.get('quantity', 1))} | Unitário: {brl(int(item.get('price_cents', 0)))} | Total: {brl(int(item.get('total_cents', 0)))}")
        total = int(order.get('total_cents', 0))
        paid = int(order.get('paid_cents', 0))
        field('Valor total', brl(total))
        field('Valor pago', brl(paid))
        field('Saldo pendente', brl(int(order.get('balance_cents', total - paid))))
    if kind == 'GARANTIA':
        paragraph('GARANTIA CONFIGURADA', True)
        delivery = order.get('delivered_at')
        days = order.get('warranty_days')
        field('Entrega efetiva', _date(delivery) if delivery else 'Entrega não registrada')
        field('Prazo em dias', days)
        expiry = 'Não calculado: entrega ou prazo não informado'
        if delivery and days is not None and days != '':
            try:
                duration = int(days)
                if duration < 0: raise ValueError
                expiry = (date.fromisoformat(str(delivery)[:10]) + timedelta(days=duration)).strftime('%d/%m/%Y')
            except (ValueError, TypeError, OverflowError):
                expiry = 'Não calculado: dados de garantia inválidos'
        field('Término', expiry)
        field('Condições informadas pela assistência', order.get('warranty_terms') or 'Condições não informadas')
    story.append(Spacer(1, 14))
    paragraph('Assinatura do cliente:')
    paragraph('________________________')
    paragraph('NÃO É DOCUMENTO FISCAL', True)

    def frame(c, doc):
        c.saveState()
        c.setFont('Helvetica', 7)
        c.setFillColor(colors.HexColor('#475569'))
        c.drawString(margin, size[1] - 8 * mm, _fit('OS ' + number + ' | ' + KINDS[kind], size[0] - margin * 2, 7))
        c.drawString(margin, 6 * mm, f'Página {doc.page} • Não é documento fiscal')
        c.restoreState()

    SimpleDocTemplate(str(path), pagesize=size, leftMargin=margin, rightMargin=margin,
                      topMargin=13 * mm, bottomMargin=12 * mm,
                      title=KINDS[kind] + ' ' + number, author=_text(company.get('name'))).build(
                          story, onFirstPage=frame, onLaterPages=frame)
    return path


def _pdf_path(path):
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError('Arquivo PDF não encontrado: ' + str(path))
    with path.open('rb') as source:
        signature = source.read(5)
    if path.suffix.lower() != '.pdf' or signature != b'%PDF-':
        raise ValueError('Selecione um arquivo PDF válido.')
    return path


def list_printers() -> list[str]:
    if sys.platform != 'win32':
        return []
    try:
        result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
                                 '[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; @(Get-Printer | Select-Object -ExpandProperty Name) | ConvertTo-Json -Compress'],
                                capture_output=True, text=True, encoding='utf-8', timeout=20, check=True)
    except (OSError, subprocess.SubprocessError) as error:
        raise RuntimeError('Não foi possível consultar as impressoras do Windows. Verifique o serviço de impressão e os drivers.') from error
    names = json.loads(result.stdout or '[]')
    return [names] if isinstance(names, str) else list(names or [])


def print_document(path, printer) -> None:
    path = _pdf_path(path)
    if sys.platform != 'win32':
        raise RuntimeError('Impressão direta disponível no Windows. Abra o PDF para imprimir.')
    if not isinstance(printer, str) or not printer.strip() or any(c in printer for c in ('"', '\r', '\n', '\x00')):
        raise ValueError('Selecione uma impressora válida.')
    if printer not in list_printers():
        raise ValueError('A impressora selecionada não está disponível.')
    execute = ctypes.windll.shell32.ShellExecuteW
    execute.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_int]
    execute.restype = ctypes.c_void_p
    result = execute(None, 'printto', str(path), '"' + printer + '"', None, 1)
    if not result or result <= 32:
        raise RuntimeError('Não foi possível imprimir pelo leitor PDF associado. Instale ou configure um leitor com suporte a impressão; você também pode abrir ou exportar o PDF e imprimir pelo leitor.')


def open_document(path) -> None:
    path = _pdf_path(path)
    try:
        if sys.platform == 'win32':
            os.startfile(str(path))
        else:
            subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', str(path)])
    except OSError as exc:
        raise RuntimeError('Não foi possível abrir o PDF. Instale um leitor PDF ou use o arquivo exportado.') from exc
