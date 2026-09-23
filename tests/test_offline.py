from types import SimpleNamespace
from orcaprime.ui import App
import os
import pytest


def test_offline_actions_do_not_require_activation():
    app = App.__new__(App)
    app.license = None
    app.actor = {"id": 0, "role": "ADMIN"}
    app.current_page = None
    calls = []
    app.safe(lambda: calls.append('saved'))()
    assert calls == ['saved']


def test_offline_has_no_license_timers():
    app = App.__new__(App)
    app.license = None
    app.actor = {"id": 0, "role": "ADMIN"}
    app.current_page = None
    app.main_visible = True
    app.generation = 1
    def unexpected(*args):
        raise AssertionError('Offline mode must not schedule license checks')
    app.root = SimpleNamespace(after=unexpected)
    app.watch(1)
    app.revalidate(1)


@pytest.mark.skipif(os.name != 'nt' and not os.environ.get('DISPLAY'), reason='Requires display')
def test_offline_opens_dashboard_without_network(tmp_path, monkeypatch):
    import tkinter as tk
    import requests
    from orcaprime.storage import Store
    def no_network(*args, **kwargs):
        raise AssertionError('Offline app attempted network access')
    monkeypatch.setattr(requests.sessions.Session, 'request', no_network)
    root = tk.Tk()
    try:
        app = App(root, Store(tmp_path / 'offline.db'))
        root.update()
        assert app.main_visible
        assert app.activation_host is None
        app.navigate('license')
        root.update()
        assert app.nav_buttons['license']['text'] == 'Sobre o OrçaPrime'
    finally:
        root.destroy()
