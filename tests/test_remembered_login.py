import pytest
from orcaprime.storage import Store
from orcaprime.users import Users
from orcaprime.remembered_login import RememberedLogin


def test_saved_login_revoked_by_password_change(tmp_path):
    users=Users(Store(tmp_path/'app.db'));actor=users.bootstrap('admin','long-password')
    saved=RememberedLogin(tmp_path);
    import json
    from orcaprime.vault import protect
    saved.path.write_bytes(protect(json.dumps({'username':'admin','password':'long-password','automatic':True}).encode()))
    assert saved.load()['automatic'] is True
    assert users.authenticate(**{k:saved.load()[k] for k in ('username','password')})['id']==actor['id']
    users.save(actor,{'username':'admin','name':'Admin','role':'ADMIN','active':True,'password':'new-long-password'},actor['id'])
    with pytest.raises(ValueError):users.authenticate(saved.load()['username'],saved.load()['password'])
    saved.clear();assert saved.load() is None


def test_corrupted_saved_login_is_discarded(tmp_path):
    saved=RememberedLogin(tmp_path);saved.path.write_bytes(b'not encrypted')
    assert saved.load() is None
    assert not saved.path.exists()


@pytest.mark.skipif(__import__('os').name!='nt',reason='Windows DPAPI')
def test_windows_credentials_are_encrypted(tmp_path):
    saved=RememberedLogin(tmp_path)
    saved.save('admin','Secret test password',True)
    assert b'Secret test password' not in saved.path.read_bytes()
    assert saved.load()=={'username':'admin','password':'Secret test password','automatic':True}
    saved.clear();assert saved.load() is None
