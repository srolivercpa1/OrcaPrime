from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

STATUSES = ('RASCUNHO', 'ENVIADO', 'APROVADO', 'RECUSADO')

def number(value):
    text = str(value).strip()
    if ',' in text:
        text = text.replace('.', '').replace(',', '.')
    try:
        result = Decimal(text)
        if not result.is_finite() or result < 0 or result > Decimal('1000000000'):
            raise ValueError('Valor fora do intervalo permitido.')
        return result
    except (InvalidOperation, ValueError):
        raise ValueError('Informe um número válido e não negativo.') from None

def money(value):
    return int((number(value) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

def brl(cents):
    return f'R$ {Decimal(int(cents))/100:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')

def decimal_text(cents):
    return f'{Decimal(int(cents))/100:.2f}'.replace('.', ',')

def line_total(item):
    qty = number(item['quantity'])
    if qty <= 0 or qty > 1000000:
        raise ValueError('Quantidade deve ser maior que zero e até 1.000.000.')
    return int((qty * money(item['price'])).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

def calculate(items, discount=0):
    if not items: raise ValueError('Adicione pelo menos um item ao orçamento.')
    subtotal = sum(line_total(item) for item in items)
    deducted = money(discount)
    if deducted > subtotal: raise ValueError('O desconto não pode superar o subtotal.')
    return subtotal, deducted, subtotal - deducted
