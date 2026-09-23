from orcaprime.storage import Store
from orcaprime.workshop import Workshop
import pytest


def test_installments_total_and_month_end(tmp_path):
    w=Workshop(Store(tmp_path/'app.db'))
    ids=w.save_installments({'description':'Compra','kind':'PAGAR','amount':'100','installments':3,'due_date':'2026-01-31'})
    rows=sorted(w.list_accounts(),key=lambda x:x['id'])
    assert len(ids)==3 and sum(r['amount_cents'] for r in rows)==10000
    assert [r['due_date'] for r in rows]==['2026-01-31','2026-02-28','2026-03-31']


def test_drawer_counts_only_cash_and_requires_discrepancy_note(tmp_path):
    w=Workshop(Store(tmp_path/'app.db'));w.open_cash('100')
    with pytest.raises(ValueError):w.open_cash('100')
    for method in ('DINHEIRO','PIX'):w.cash_entry({'description':'Entrada','kind':'ENTRADA','amount':'50','method':method})
    with pytest.raises(ValueError):w.close_cash('140')
    w.close_cash('140','Falta apurada')
    row=w.list_cash_sessions()[0]
    assert row['expected_cents']==15000 and row['difference_cents']==-1000
