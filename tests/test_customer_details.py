from orcaprime.storage import Store

def test_extended_customer_fields_survive_edit_and_restart(tmp_path):
    store=Store(tmp_path/'db')
    details=dict(name='Maria',person_type='Pessoa física',whatsapp='64999999999',secondary_phone='6433333333',contact_name='João',postal_code='75900000',neighborhood='Centro',city='Rio Verde',state='GO',notes='Prefere contato à tarde')
    cid=store.save_customer(details)
    reloaded=Store(tmp_path/'db').list_customers()[0]
    for key,value in details.items():assert reloaded.get(key)==value
    store.save_customer({'name':'Maria Silva'},cid)
    assert store.list_customers()[0]['whatsapp']==details['whatsapp']
    assert store.list_customers()[0]['notes']==details['notes']
