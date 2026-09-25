"""A commercial build must never silently fall back to an unlicensed session."""
import json
from pathlib import Path
from .license_client import LicenseClient


def configured_client(base, data_dir):
    path=Path(base)/'config'/'client.json'
    try:
        configuration=json.loads(path.read_text(encoding='utf-8'))
        return LicenseClient(configuration,data_dir)
    except (OSError,ValueError,TypeError,AttributeError) as error:
        raise ValueError('Este instalador está sem configuração válida de licenciamento. Solicite o instalador oficial à Sketch Inc.') from error
