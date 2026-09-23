import pytest
from orcaprime.storage import Store
from orcaprime.users import Users


def test_first_admin_and_authentication(tmp_path):
    users=Users(Store(tmp_path/'app.db'))
    assert not users.has_users()
    admin=users.bootstrap('gestor','SenhaSegura123')
    assert users.authenticate('gestor','SenhaSegura123')['role']=='ADMIN'
    with pytest.raises(ValueError):users.bootstrap('outro','SenhaSegura123')
    with pytest.raises(ValueError):users.authenticate('gestor','errada')
    assert 'password' not in admin


def test_permissions_and_last_admin(tmp_path):
    users=Users(Store(tmp_path/'app.db'))
    admin=users.bootstrap('gestor','SenhaSegura123')
    tech=users.save(admin,{'username':'tecnico','name':'Técnico','role':'TECNICO','password':'SenhaSegura123'})
    technician=users.authenticate('tecnico','SenhaSegura123')
    with pytest.raises(ValueError):users.save(technician,{'username':'x','password':'SenhaSegura123','role':'ADMIN'})
    with pytest.raises(ValueError):users.save(admin,{'username':'gestor','name':'Gestor','role':'TECNICO','active':True},admin['id'])
    users.save(admin,{'username':'tecnico','name':'Técnico','role':'TECNICO','active':False},tech)
    with pytest.raises(ValueError):users.authenticate('tecnico','SenhaSegura123')
