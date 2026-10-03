import io
import base64
from datetime import datetime,timezone
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import mm


def order_pdf(company,customer,order,kind):
    output=io.BytesIO();doc=SimpleDocTemplate(output,rightMargin=18*mm,leftMargin=18*mm,topMargin=15*mm,bottomMargin=15*mm)
    styles=getSampleStyleSheet();elements=[]
    def line(text,style='BodyText'):
        elements.append(Paragraph(escape(str(text)).replace('\n','<br/>'),styles[style]));elements.append(Spacer(1,5*mm))
    if company.settings.get('logo'):
        logo=Image(io.BytesIO(base64.b64decode(company.settings['logo'])))
        logo._restrictSize(45*mm,20*mm);elements.append(logo)
    line(company.name,'Title')
    line(' • '.join(company.settings.get(k,'') for k in ('document','phone','address') if company.settings.get(k)))
    line(('TERMO DE GARANTIA' if kind=='garantia' else 'ORDEM DE SERVIÇO')+' #'+order['id'][:8].upper(),'Heading1')
    line('Cliente: '+customer['name']+' | '+customer.get('phone',''))
    line('Aparelho: '+order['device']+' | '+order.get('brand','')+' | Série/IMEI: '+order.get('serial',''))
    line('Entrada: '+datetime.fromtimestamp(order['created'],timezone.utc).strftime('%d/%m/%Y'))
    for title,key in [('Defeito relatado','description'),('Acessórios','accessories'),('Serviços executados','service')]:
        line(title,'Heading3');line(order.get(key,'') or 'Não informado')
    if order.get('parts'):
        line('Peças utilizadas','Heading3')
        for p in order['parts']:line(str(p['quantity'])+' × '+p['name'])
    line('Valor total: R$ '+f"{order['amount']/100:,.2f}".replace(',','X').replace('.',',').replace('X','.'))
    if kind=='garantia':
        line('Prazo de garantia informado pela assistência: '+str(order['warranty'])+' dias.')
        line(company.settings.get('warranty_text','Consulte as condições de garantia acordadas com a assistência.'))
    line('Assinatura do cliente: ____________________________________')
    line('OrçaPrime 1.0 • Desenvolvido por Sketch Inc • Documento não fiscal')
    doc.build(elements);return output.getvalue()
