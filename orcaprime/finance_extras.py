"""Parcelas mensais e conferência de caixa em dinheiro, sem somar PIX ao numerário."""
import calendar
import json
from datetime import date,datetime
from decimal import Decimal,InvalidOperation,ROUND_HALF_UP


def cents(value):
    try:
        n=Decimal(str(value).replace(',','.'))
        if not n.is_finite() or n<0 or n>1000000000:raise ValueError()
        return int((n*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
    except (ValueError,InvalidOperation):raise ValueError('Informe um valor válido.') from None


class FinanceExtras:
    def save_installments(self,data):
        self._allow('FINANCEIRO')
        try:n=int(data.get('installments',1));start=date.fromisoformat(data.get('due_date',''))
        except (ValueError,TypeError):raise ValueError('Informe parcelas e vencimento válidos.') from None
        amount=cents(data.get('amount',0));kind=data.get('kind');description=str(data.get('description','')).strip()
        if not 1<=n<=60 or amount<n or kind not in ('PAGAR','RECEBER') or not description:raise ValueError('Confira valor, tipo, descrição e quantidade de parcelas (1 a 60).')
        ids=[];base,remainder=divmod(amount,n)
        with self.connect() as db:
            for i in range(n):
                total_months=start.year*12+start.month-1+i;year,month=divmod(total_months,12);month+=1
                due=date(year,month,min(start.day,calendar.monthrange(year,month)[1]))
                d={'description':f'{description} ({i+1}/{n})' if n>1 else description,'kind':kind,'due_date':due.isoformat(),'created_at':datetime.now().isoformat(timespec='seconds'),'actor':dict(self.actor),'installment':i+1,'installments':n}
                ids.append(db.execute('INSERT INTO ws_accounts(data,amount_cents) VALUES(?,?)',(json.dumps(d,ensure_ascii=False),base+(i<remainder))).lastrowid)
        return ids
    def _sessions(self,db):
        db.execute('''CREATE TABLE IF NOT EXISTS ws_cash_sessions(
            id INTEGER PRIMARY KEY,opened_at TEXT NOT NULL,opening_cents INTEGER NOT NULL,
            start_entry INTEGER NOT NULL,closed_at TEXT,expected_cents INTEGER,counted_cents INTEGER,
            difference_cents INTEGER,end_entry INTEGER,note TEXT NOT NULL DEFAULT '',actor TEXT NOT NULL)''')
    def open_cash(self,opening_amount):
        self._allow('FINANCEIRO');opening=cents(opening_amount)
        with self.connect() as db:
            self._sessions(db)
            if db.execute('SELECT 1 FROM ws_cash_sessions WHERE closed_at IS NULL').fetchone():raise ValueError('Já existe um caixa aberto.')
            last=db.execute('SELECT COALESCE(MAX(id),0) FROM ws_cash').fetchone()[0]
            return db.execute('INSERT INTO ws_cash_sessions(opened_at,opening_cents,start_entry,actor) VALUES(?,?,?,?)',(datetime.now().isoformat(timespec='seconds'),opening,last,json.dumps({'opened_by':self.actor},ensure_ascii=False))).lastrowid
    def close_cash(self,counted_amount,note=''):
        self._allow('FINANCEIRO');counted=cents(counted_amount)
        with self.connect() as db:
            self._sessions(db)
            row=db.execute('SELECT * FROM ws_cash_sessions WHERE closed_at IS NULL').fetchone()
            if not row:raise ValueError('Não há caixa aberto.')
            expected=row['opening_cents']
            for amount,raw in db.execute('SELECT amount_cents,data FROM ws_cash WHERE id>?',(row['start_entry'],)):
                if json.loads(raw).get('method','').upper()=='DINHEIRO':expected+=amount
            difference=counted-expected
            if difference and not str(note).strip():raise ValueError('Justifique a diferença na conferência do caixa.')
            last=db.execute('SELECT COALESCE(MAX(id),0) FROM ws_cash').fetchone()[0]
            actors=json.loads(row['actor']);actors['closed_by']=dict(self.actor)
            db.execute('UPDATE ws_cash_sessions SET closed_at=?,expected_cents=?,counted_cents=?,difference_cents=?,end_entry=?,note=?,actor=? WHERE id=?',(datetime.now().isoformat(timespec='seconds'),expected,counted,difference,last,str(note).strip(),json.dumps(actors,ensure_ascii=False),row['id']))
            return row['id']
    def list_cash_sessions(self):
        self._allow('FINANCEIRO')
        with self.connect() as db:
            self._sessions(db)
            return [dict(row) for row in db.execute('SELECT * FROM ws_cash_sessions ORDER BY id DESC')]


def validate_finance_database(db):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='ws_cash_sessions'").fetchone():return
    active=0
    for row in db.execute('SELECT opened_at,opening_cents,start_entry,closed_at,expected_cents,counted_cents,difference_cents,note,actor,end_entry FROM ws_cash_sessions'):
        opened,opening,start,closed,expected,counted,difference,note,actor,end=row
        datetime.fromisoformat(opened)
        if type(opening) is not int or opening<0 or type(start) is not int or start<0 or not isinstance(json.loads(actor),dict):raise ValueError('Caixa inválido no backup.')
        if closed:
            datetime.fromisoformat(closed)
            if type(end) is not int or end<start:raise ValueError('Intervalo de caixa inválido.')
            actual=opening+sum(amount for amount,raw in db.execute('SELECT amount_cents,data FROM ws_cash WHERE id>? AND id<=?',(start,end)) if json.loads(raw).get('method','').upper()=='DINHEIRO')
            if actual!=expected:raise ValueError('Saldo de conferência incompatível com o livro-caixa.')
            if any(type(n) is not int for n in (expected,counted,difference)) or counted<0 or counted-expected!=difference:raise ValueError('Fechamento de caixa inconsistente.')
        else:active+=1
    if active>1:raise ValueError('Mais de um caixa aberto no backup.')
