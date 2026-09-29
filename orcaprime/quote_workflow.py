"""Service tracking for quotes without replacing their commercial situation."""
import json
from datetime import datetime

SERVICE_STATUSES={'AGUARDANDO':'Aguardando','EM_ANDAMENTO':'Em andamento','PRONTO':'Pronto','ENTREGUE':'Entregue'}

class QuoteWorkflow:
    def delete_quote(self,id_):
        with self.connect() as db:
            if db.execute('DELETE FROM quotes WHERE id=?',(id_,)).rowcount!=1:
                raise ValueError('Orçamento não encontrado.')

    def set_service_status(self,ids,status,note='',actor=''):
        ids=list(dict.fromkeys(ids))
        if not ids or len(ids)>500 or status not in SERVICE_STATUSES:raise ValueError('Selecione os registros e uma situação válida.')
        at=datetime.now().astimezone().isoformat(timespec='seconds')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            records=[]
            for id_ in ids:
                row=db.execute('SELECT data FROM quotes WHERE id=?',(id_,)).fetchone()
                if not row:raise ValueError('Orçamento não encontrado.')
                q=json.loads(row[0])
                previous=q.get('service_status','AGUARDANDO')
                if previous=='ENTREGUE' and status!='ENTREGUE':raise ValueError('Atendimento entregue é mantido no histórico. Duplique para um novo atendimento.')
                records.append((id_,q,previous))
            for id_,q,previous in records:
                if previous==status:continue
                q['service_status']=status
                q.setdefault('service_history',[]).append({'at':at,'from':previous,'to':status,'note':str(note).strip()[:4000],'actor':str(actor)[:200]})
                if status=='ENTREGUE':q['delivered_at']=at
                db.execute('UPDATE quotes SET data=? WHERE id=?',(json.dumps(q,ensure_ascii=False),id_))

    def customer_order_ids(self,id_):
        with self.connect() as db:
            if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='ws_orders'").fetchone():return ()
            return tuple(row[0] for row in db.execute('SELECT id FROM ws_orders WHERE customer_id=? ORDER BY id',(id_,)))

    def delete_customer(self,id_,expected_orders=None):
        with self.connect() as db:
            db.execute('PRAGMA foreign_keys=ON');db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT data FROM customers WHERE id=?',(id_,)).fetchone()
            if not row:raise ValueError('Cliente não encontrado.')
            has_orders=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='ws_orders'").fetchone()
            if has_orders:
                ids=tuple(r[0] for r in db.execute('SELECT id FROM ws_orders WHERE customer_id=? ORDER BY id',(id_,)))
                if expected_orders is not None and ids!=tuple(expected_orders):raise ValueError('As OS do cliente mudaram. Confira e confirme a exclusão novamente.')
                # Keep real cash and inventory balances, removing only their links.
                db.execute('UPDATE ws_cash SET payment_id=NULL WHERE payment_id IN (SELECT id FROM ws_payments WHERE order_id IN (SELECT id FROM ws_orders WHERE customer_id=?))',(id_,))
                db.execute('UPDATE ws_movements SET order_id=NULL WHERE order_id IN (SELECT id FROM ws_orders WHERE customer_id=?)',(id_,))
                for table in ('ws_attachments','ws_events','ws_items','ws_payments'):
                    db.execute(f'DELETE FROM {table} WHERE order_id IN (SELECT id FROM ws_orders WHERE customer_id=?)',(id_,))
                db.execute('UPDATE ws_orders SET parent_id=NULL WHERE parent_id IN (SELECT id FROM ws_orders WHERE customer_id=?)',(id_,))
                db.execute('DELETE FROM ws_orders WHERE customer_id=?',(id_,))
            customer=json.loads(row[0])
            customer['deleted_at']=datetime.now().astimezone().isoformat(timespec='seconds')
            db.execute('UPDATE customers SET data=? WHERE id=?',(json.dumps(customer,ensure_ascii=False),id_))



def report_text(q):
    from .domain import brl
    def when(value):
        return datetime.fromisoformat(value).strftime('%d/%m/%Y %H:%M') if value else 'Não informado'
    c=q['customer']
    lines=['RELATÓRIO DO ATENDIMENTO '+q['number'],
           'Cliente: '+c['name'],'Documento: '+c.get('document',''),
           'Contato: '+ ' / '.join(filter(None,[c.get('phone'),c.get('whatsapp'),c.get('email')])),
           'Endereço: '+ ' / '.join(filter(None,[c.get('address'),c.get('neighborhood'),c.get('city'),c.get('state'),c.get('postal_code')])),
           'Aparelho: '+(q.get('equipment') or 'Não informado'),'Serial / IMEI: '+(q.get('serial') or 'Não informado'),
           'Criação: '+q['created_at'],'Validade: '+q['valid_until'],
           'Situação comercial: '+q['status'],'Andamento: '+SERVICE_STATUSES[q.get('service_status','AGUARDANDO')],
           'Entregue em: '+when(q.get('delivered_at')),'','SERVIÇOS / ITENS']
    for item in q['items']:lines.append(f"{item['description']} | {item['quantity']} {item['unit']} | {brl(item['total_cents'])}")
    lines.extend(['Subtotal: '+brl(q['subtotal_cents']),'Desconto: '+brl(q['discount_cents']),'Total: '+brl(q['total_cents']),
                  '', 'RELATO DO SERVIÇO',q.get('service_report') or 'Não informado','', 'OBSERVAÇÕES',q.get('notes',''),'', 'CONDIÇÕES',q.get('terms',''),'', 'HISTÓRICO'])
    for event in q.get('service_history',[]):lines.append(f"{when(event['at'])} | {SERVICE_STATUSES[event['to']]} | {event.get('actor','')}\n{event.get('note','')}")
    return '\n'.join(lines)
