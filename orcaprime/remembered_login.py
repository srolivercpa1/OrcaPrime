"""Opt-in remembered credentials bound to the current Windows user by DPAPI."""
import json
import os
from pathlib import Path
from .vault import protect, unprotect


class RememberedLogin:
    def __init__(self, directory):
        self.path = Path(directory) / 'remembered-login.dat'

    def clear(self):
        self.path.unlink(missing_ok=True)

    def load(self):
        if not self.path.exists():
            return None
        try:
            if self.path.stat().st_size > 16384:
                raise ValueError('Arquivo inválido')
            data = json.loads(unprotect(self.path.read_bytes()))
            if not isinstance(data.get('username'), str) or not isinstance(data.get('password'), str):
                raise ValueError('Dados inválidos')
            if not isinstance(data.get('automatic'), bool):
                raise ValueError('Preferência inválida')
            return data
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            self.clear()
            return None

    def save(self, username, password, automatic=False):
        if os.name != 'nt':
            raise OSError('Salvar acesso está disponível somente no Windows com proteção DPAPI.')
        data = json.dumps({'username': username, 'password': password, 'automatic': bool(automatic)}).encode()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix('.tmp')
        try:
            temporary.write_bytes(protect(data))
            temporary.replace(self.path)
        finally:
            temporary.unlink(missing_ok=True)
