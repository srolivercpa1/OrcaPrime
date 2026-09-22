from html import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from .domain import brl

def export_quote(path,quote,company):
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='SmallPrime',fontName='Helvetica',fontSize=9,leading=13,textColor=colors.HexColor('#334155')))
    def p(text,style='SmallPrime'): return Paragraph(escape(str(text)).replace('\n','<br/>'),styles[style])
    def date_br(v): return '/'.join(v.split('-')[::-1])
    story=[p(company.get('name') or 'Sua empresa','Title'),p(' • '.join(filter(None,[company.get('document'),company.get('phone'),company.get('email')]))),p(company.get('address','')),Spacer(1,20),p('ORÇAMENTO '+quote['number'],'Heading1'),p(f"Emissão: {date_br(quote['created_at'])} | Validade: {date_br(quote['valid_until'])} | {quote['status']}"),Spacer(1,12)]
    c=quote['customer'];story.extend([p('CLIENTE','Heading3'),p(c['name']),p(' • '.join(filter(None,[c.get('document'),c.get('phone'),c.get('email')]))),p(c.get('address','')),Spacer(1,16)])
    rows=[[p(v) for v in ('Descrição','Qtd.','Un.','Unitário','Total')]]
    for i in quote['items']:
        from .domain import money
        rows.append([p(i['description']),p(i['quantity'].replace('.',',')),p(i['unit']),p(brl(money(i['price']))),p(brl(i['total_cents']))])
    table=Table(rows,colWidths=[230,48,32,90,90],repeatRows=1,hAlign='LEFT',splitInRow=1)
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e2e8f0')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8fafc')]),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,0),1,colors.HexColor('#14b8a6'))]))
    story.extend([table,Spacer(1,15),p('Subtotal: '+brl(quote['subtotal_cents'])),p('Desconto: '+brl(quote['discount_cents'])),p('TOTAL: '+brl(quote['total_cents']),'Heading2')])
    for title,key in [('Condições de pagamento','terms'),('Observações','notes')]:
        if quote.get(key): story.extend([p(title,'Heading3'),p(quote[key])])
    story.extend([Spacer(1,30),p('Aprovação do cliente: ___________________________________'),p('Orçamento comercial. Não é documento fiscal.')])
    def footer(canvas,doc):
        canvas.saveState();canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#64748b'))
        canvas.drawString(42,24,'OrçaPrime • OLIVERTECH SOLUÇÕES');canvas.drawRightString(A4[0]-42,24,f'Página {doc.page}');canvas.restoreState()
    SimpleDocTemplate(str(path),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=36,bottomMargin=45,title='Orçamento '+quote['number'],author=company.get('name','')).build(story,onFirstPage=footer,onLaterPages=footer)
