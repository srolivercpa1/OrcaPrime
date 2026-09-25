import pytest
from orcaprime.client_configuration import configured_client


def test_missing_or_invalid_configuration_fails_closed(tmp_path):
    with pytest.raises(ValueError,match='instalador oficial'):
        configured_client(tmp_path,tmp_path/'data')
    (tmp_path/'config').mkdir()
    (tmp_path/'config/client.json').write_text('{"license_url":"http://unsafe", "public_key":"bad"}')
    with pytest.raises(ValueError,match='instalador oficial'):
        configured_client(tmp_path,tmp_path/'data')
