"""Pure, date-explicit queries for the workshop. Authorization belongs to Workshop."""
from dataclasses import dataclass
from datetime import date

CLOSED = {'ENTREGUE', 'CANCELADA'}
PRIORITIES = ('BAIXA', 'NORMAL', 'ALTA', 'URGENTE')

@dataclass(frozen=True)
class OrderFilters:
    text: str = ''
    status: str = ''
    technician: str = ''
    priority: str = ''
    deadline: str = ''
    returns_only: bool = False
    active_only: bool = False


def parsed_date(value):
    try:
        return date.fromisoformat(str(value)) if value else None
    except (ValueError, TypeError):
        return None


def priority(order):
    return str(order.get('priority') or 'NORMAL').strip().upper()


def filter_orders(orders, filters, today):
    result = []
    for order in orders:
        text = ' '.join(str(order.get(k) or '') for k in ('number','equipment','brand','model','serial'))
        text += ' ' + str((order.get('customer') or {}).get('name') or '')
        if filters.text.strip().casefold() not in text.casefold(): continue
        if filters.status and order.get('status') != filters.status: continue
        if filters.technician and str(order.get('technician') or '').strip().casefold() != filters.technician.strip().casefold(): continue
        if filters.priority and priority(order) != filters.priority: continue
        if filters.active_only and order.get('status') in CLOSED: continue
        if filters.returns_only and not order.get('parent_id'): continue
        due = parsed_date(order.get('due_date'))
        active = order.get('status') not in CLOSED
        if filters.deadline == 'overdue' and not (active and due and due < today): continue
        if filters.deadline == 'today' and not (active and due == today): continue
        if filters.deadline == 'undated' and order.get('due_date'): continue
        result.append(order)
    return result


def summarize_orders(orders, today):
    active = [o for o in orders if o.get('status') not in CLOSED]
    return {
        'active': len(active),
        'overdue': len(filter_orders(active, OrderFilters(deadline='overdue'), today)),
        'awaiting_approval': sum(o.get('status') == 'AGUARDANDO_APROVACAO' for o in active),
        'ready': sum(o.get('status') == 'PRONTA' for o in active),
        'invalid_dates': sum(bool(o.get('due_date')) and parsed_date(o['due_date']) is None for o in active),
        'due_today': filter_orders(active, OrderFilters(deadline='today'), today),
        'agenda': sorted([o for o in active if parsed_date(o.get('due_date'))], key=lambda o:o['due_date']),
    }


def equipment_history(orders, customer_id, serial):
    serial = str(serial or '').strip()
    return {'scope': 'equipment' if serial else 'customer',
            'orders': [o for o in orders if o.get('customer_id') == customer_id and
                       (not serial or str(o.get('serial') or '').strip() == serial)]}


def productivity(orders, start, end):
    if start > end: raise ValueError('A data inicial deve ser anterior ou igual à data final.')
    grouped = {}
    for order in orders:
        delivered = [parsed_date(str(e.get('created_at') or '').split('T')[0].split(' ')[0]) for e in order.get('events', [])
                     if e.get('action') == 'SITUACAO' and e.get('target') == 'ENTREGUE']
        dates = [d for d in delivered if d]
        if not dates or not start <= min(dates) <= end: continue
        name = str(order.get('technician') or '').strip() or 'Sem técnico'
        ids = grouped.setdefault(name, [])
        if order['id'] not in ids: ids.append(order['id'])
    return [dict(technician=name, delivered_count=len(ids), delivered_order_ids=ids)
            for name,ids in sorted(grouped.items())]
