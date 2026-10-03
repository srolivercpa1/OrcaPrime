"""One-time owner enrollment guarded by a privately provisioned installation code."""
import secrets
from pathlib import Path
from fastapi import Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from .db import User, Audit
from .security import create_owner, digest


class SetupInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    token: str = Field(min_length=1, max_length=512)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=12, max_length=200)


def register(app, db_dep, setup_token):
    expected = digest(setup_token) if setup_token and len(setup_token) >= 32 else None

    @app.get('/setup')
    def setup_page():
        return FileResponse(Path(__file__).parent / 'static' / 'setup.html')

    @app.get('/api/setup')
    def status(db=Depends(db_dep)):
        return {'available': bool(expected and not db.scalar(select(User.id).where(User.role == 'OWNER')))}

    @app.post('/api/setup', status_code=201)
    def setup(data: SetupInput, db=Depends(db_dep)):
        if not expected:
            raise HTTPException(404, 'Configuração inicial indisponível.')
        if not secrets.compare_digest(digest(data.token), expected):
            raise HTTPException(403, 'Código de instalação inválido.')
        if db.scalar(select(User.id).where(User.role == 'OWNER')):
            raise HTTPException(409, 'O proprietário já foi configurado. Entre na sua conta.')
        try:
            owner = create_owner(db, data.email, data.password)
        except ValueError as error:
            raise HTTPException(422, str(error)) from None
        db.add(Audit(actor=owner.id, action='CONFIGURAR_PROPRIETARIO', target=owner.id))
        return {'ok': True}
