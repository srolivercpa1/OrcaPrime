"""Company fiscal profiles. Saving a profile does not authorize invoice issuance.

Credentials/certificates are deliberately not part of this nonsecret model.
CNPJ check digits follow RFB IN 2.229/2024, Anexo XV (ASCII minus 48).
"""
import re
from typing import Literal

from fastapi import Depends
from pydantic import Field, field_validator, model_validator

from .api import Input
from .db import Company

STATE_CODES = dict(zip(
    'RO AC AM RR PA AP TO MA PI CE RN PB PE AL SE BA MG ES RJ SP PR SC RS MS MT GO DF'.split(),
    '11 12 13 14 15 16 17 21 22 23 24 25 26 27 28 29 31 32 33 35 41 42 43 50 51 52 53'.split(),
))


class FiscalSettings(Input):
    legal_name: str = Field(default='', max_length=160)
    trade_name: str = Field(default='', max_length=160)
    cnpj: str = Field(default='', max_length=18)
    state_registration: str = Field(default='', max_length=30)
    municipal_registration: str = Field(default='', max_length=30)
    tax_regime: Literal['', '1', '2', '3', '4'] = ''
    street: str = Field(default='', max_length=160)
    number: str = Field(default='', max_length=30)
    complement: str = Field(default='', max_length=100)
    district: str = Field(default='', max_length=100)
    city: str = Field(default='', max_length=100)
    state: str = Field(default='', max_length=2)
    municipality_code: str = Field(default='', pattern=r'^([0-9]{7})?$')
    postal_code: str = Field(default='', max_length=9)
    environment: Literal['homologation', 'production'] = 'homologation'
    series: int = Field(default=1, ge=0, le=999, strict=True)
    next_number: int = Field(default=1, ge=1, le=999999999, strict=True)

    @field_validator('cnpj')
    @classmethod
    def validate_cnpj(cls, value):
        value = re.sub(r'[./\-]', '', value).upper()
        if not value:
            return value
        if not re.fullmatch(r'[A-Z0-9]{12}[0-9]{2}', value) or len(set(value)) == 1:
            raise ValueError('CNPJ inválido.')
        digits = value[:12]
        for weights in ((5,4,3,2,9,8,7,6,5,4,3,2), (6,5,4,3,2,9,8,7,6,5,4,3,2)):
            remainder = sum((ord(char)-48)*weight for char,weight in zip(digits,weights)) % 11
            digits += str(0 if remainder < 2 else 11-remainder)
        if digits != value:
            raise ValueError('Dígitos verificadores do CNPJ inválidos.')
        return value

    @field_validator('state')
    @classmethod
    def validate_state(cls, value):
        value = value.upper()
        if value and value not in STATE_CODES:
            raise ValueError('UF inválida.')
        return value

    @field_validator('postal_code')
    @classmethod
    def validate_postal_code(cls, value):
        value = value.replace('-', '')
        if value and not re.fullmatch(r'[0-9]{8}', value):
            raise ValueError('CEP inválido.')
        return value

    @model_validator(mode='after')
    def check_municipality_state(self):
        if self.state and self.municipality_code and not self.municipality_code.startswith(STATE_CODES[self.state]):
            raise ValueError('Código IBGE incompatível com a UF.')
        return self


def profile_response(settings):
    required = ('legal_name','cnpj','tax_regime','street','number','district','city','state','municipality_code','postal_code')
    missing = [key for key in required if not settings[key]]
    return {'settings':settings, 'missing_fields':missing, 'profile_complete':not missing,
            'integration':'not_connected', 'can_emit':False}


def register(app, db_dep, actor, require, audit):
    @app.get('/api/fiscal')
    def fiscal_settings(user=Depends(actor), db=Depends(db_dep)):
        require(user, 'ADMIN')
        company = db.get(Company, user.company_id)
        settings = FiscalSettings.model_validate(company.settings.get('fiscal', {})).model_dump()
        return profile_response(settings)

    @app.put('/api/fiscal')
    def save_fiscal_settings(data:FiscalSettings, user=Depends(actor), db=Depends(db_dep)):
        require(user, 'ADMIN')
        company = db.get(Company, user.company_id)
        settings = data.model_dump()
        company.settings = {**company.settings, 'fiscal':settings}
        audit(db, user, 'CONFIGURAR_FISCAL', company.id)
        return profile_response(settings)
