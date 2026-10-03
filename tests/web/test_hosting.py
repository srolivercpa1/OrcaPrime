"""Deployment checks use throwaway databases; never point at production."""
import os
from concurrent.futures import ThreadPoolExecutor
import threading

import pytest
pytest.importorskip('sqlalchemy')
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from webapp.api import create_app
from webapp.db import Base, User, Session, Company, Photo
from webapp.security import verify_password

TOKEN = 'installation-test-only-' + 'a' * 32
FORM = {'token': TOKEN, 'email': 'owner@example.test', 'password': 'Private-password-123'}


@pytest.fixture
def empty_url(tmp_path):
    url = os.environ.get('ORCAPRIME_TEST_DATABASE') or 'sqlite:///' + str(tmp_path / 'hosting.db')
    engine = create_engine(url)
    Base.metadata.drop_all(engine)
    engine.dispose()
    return url


def test_setup_requires_secret_and_can_only_run_once(empty_url):
    app = create_app(empty_url, setup_token=TOKEN)
    client = TestClient(app)
    assert client.get('/api/setup').json() == {'available': True}
    assert client.get('/setup').status_code == 200
    assert client.post('/api/setup', json={**FORM, 'token': 'wrong'}).status_code == 403
    assert client.post('/api/setup', json=FORM, headers={'Origin': 'https://untrusted.test'}).status_code == 403
    invalid = client.post('/api/setup', json={**FORM, 'password': 'tiny-secret'})
    assert invalid.status_code == 422
    assert TOKEN not in invalid.text and 'tiny-secret' not in invalid.text
    result = client.post('/api/setup', json=FORM)
    assert result.status_code == 201, result.text
    assert TOKEN not in result.text and FORM['password'] not in result.text
    assert 'set-cookie' not in result.headers
    assert client.get('/api/setup').json() == {'available': False}
    assert client.post('/api/setup', json={**FORM, 'email': 'second@example.test'}).status_code == 409
    with app.state.factory() as db:
        owner = db.scalar(select(User).where(User.role == 'OWNER'))
        assert owner.email == FORM['email']
        assert owner.password != FORM['password'] and verify_password(FORM['password'], owner.password)
    assert client.post('/api/login', json={'email': FORM['email'], 'password': FORM['password']}).status_code == 200
    app.state.engine.dispose()


def test_setup_is_disabled_without_a_long_secret_and_rate_limited(empty_url):
    for token in (None, '', 'short'):
        app = create_app(empty_url, setup_token=token)
        client = TestClient(app)
        assert client.get('/api/setup').json() == {'available': False}
        assert client.post('/api/setup', json=FORM).status_code == 404
        app.state.engine.dispose()
    app = create_app(empty_url, setup_token=TOKEN)
    client = TestClient(app)
    for _ in range(30):
        assert client.post('/api/setup', json={**FORM, 'token': 'wrong'}).status_code == 403
    assert client.post('/api/setup', json=FORM).status_code == 429
    app.state.engine.dispose()


def test_concurrent_setup_creates_one_owner(empty_url):
    app = create_app(empty_url, setup_token=TOKEN)
    barrier = threading.Barrier(2)
    def before(conn, cursor, statement, parameters, context, executemany):
        if statement.startswith('INSERT INTO web_users'):
            barrier.wait(timeout=10)
    event.listen(app.state.engine, 'before_cursor_execute', before)
    def signup(email):
        return TestClient(app).post('/api/setup', json={**FORM, 'email': email}).status_code
    try:
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(signup, ['a@example.test', 'b@example.test']))
        assert sorted(results) == [201, 409]
    finally:
        event.remove(app.state.engine, 'before_cursor_execute', before)
    with app.state.factory() as db:
        assert len(list(db.scalars(select(User).where(User.role == 'OWNER')))) == 1
    app.state.engine.dispose()


def test_render_origin_is_used_without_public_origin():
    from webapp.server import production_config
    env = {'DATABASE_URL': 'postgres://u:p@db.test/orcaprime?sslmode=require', 'RENDER_EXTERNAL_URL': 'https://orcaprime-test.onrender.com/'}
    url, origin = production_config(env)
    assert url == 'postgresql+psycopg://u:p@db.test/orcaprime?sslmode=require'
    assert origin == 'https://orcaprime-test.onrender.com'
    assert production_config({**env, 'PUBLIC_ORIGIN': 'https://app.example.test'})[1] == 'https://app.example.test'
    for bad in ('http://public.example.test', 'https://app.example.test/path', 'https://user:pass@app.example.test'):
        with pytest.raises(ValueError):
            production_config({**env, 'PUBLIC_ORIGIN': bad})
    with pytest.raises(ValueError):
        production_config({**env, 'DATABASE_URL': 'sqlite:///production.db'})


def test_encrypted_backup_restores_photos_but_not_sessions(empty_url, tmp_path):
    from cryptography.fernet import Fernet
    from webapp.backup import backup, restore
    from webapp.security import bootstrap
    bootstrap(empty_url, FORM['email'], FORM['password'])
    app = create_app(empty_url)
    with app.state.factory.begin() as db:
        owner = db.scalar(select(User).where(User.role == 'OWNER'))
        db.add(Session(id='session-secret', user_id=owner.id, csrf='csrf-secret', expires=2000000000))
        db.add(Company(id='shop', name='Private shop', expires=2000000000))
        db.flush()
        db.add(Photo(company_id='shop', order_id='order', name='Private photo', content=b'private-photo-content'))
    key = Fernet.generate_key().decode()
    archive = backup(app.state.engine, tmp_path / 'backups', encryption_key=key)
    assert archive.name.endswith('.json.gz.enc')
    assert list((tmp_path / 'backups').iterdir()) == [archive]
    assert archive.stat().st_mode & 0o777 == 0o600
    assert b'private-photo-content' not in archive.read_bytes()
    destination = 'sqlite:///' + str(tmp_path / 'restored.db')
    with pytest.raises(ValueError):
        restore(destination, archive)
    with pytest.raises(ValueError):
        restore(destination, archive, encryption_key=Fernet.generate_key().decode())
    damaged = tmp_path / 'damaged.json.gz.enc'
    raw = archive.read_bytes()
    damaged.write_bytes(raw[:50] + b'!' + raw[51:])
    with pytest.raises(ValueError):
        restore(destination, damaged, encryption_key=key)
    assert not (tmp_path / 'restored.db').exists()
    restore(destination, archive, encryption_key=key)
    restored = create_app(destination)
    with restored.state.factory() as db:
        assert db.scalar(select(Photo)).content == b'private-photo-content'
        assert db.scalar(select(Session)) is None
        assert db.scalar(select(User)).email == FORM['email']
    with pytest.raises(ValueError, match='vazio'):
        restore(destination, archive, encryption_key=key)
    with pytest.raises(ValueError):
        backup(app.state.engine, tmp_path / 'invalid', encryption_key='bad-key')
    assert not list((tmp_path / 'invalid').glob('*'))
    restored.state.engine.dispose()
    app.state.engine.dispose()


def test_cli_encryption_requires_key_and_does_not_modify_source(empty_url, tmp_path, monkeypatch):
    from webapp.cli import main
    from webapp.security import bootstrap
    from cryptography.fernet import Fernet
    bootstrap(empty_url, FORM['email'], FORM['password'])
    monkeypatch.setenv('DATABASE_URL', empty_url)
    monkeypatch.delenv('BACKUP_ENCRYPTION_KEY', raising=False)
    monkeypatch.setattr('sys.argv', ['webapp.cli', 'backup', '--encrypted', '--directory', str(tmp_path / 'cli')])
    with pytest.raises(SystemExit, match='BACKUP_ENCRYPTION_KEY'):
        main()
    monkeypatch.setenv('BACKUP_ENCRYPTION_KEY', Fernet.generate_key().decode())
    statements = []
    from sqlalchemy.engine import Engine
    def before(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)
    event.listen(Engine, 'before_cursor_execute', before)
    try:
        main()
    finally:
        event.remove(Engine, 'before_cursor_execute', before)
    assert list((tmp_path / 'cli').glob('*.json.gz.enc'))
    assert all(s.lstrip().upper().startswith('SELECT') for s in statements), statements
