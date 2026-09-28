"""Shared customer fields for the directory and service-order intake."""
STATES=('', 'AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO')
CUSTOMER_FIELDS=[
    ('name','Nome completo / razão social *',None),
    ('person_type','Tipo de cliente',('Pessoa física','Pessoa jurídica')),
    ('document','CPF / CNPJ',None),
    ('phone','Telefone principal',None),
    ('whatsapp','WhatsApp',None),
    ('secondary_phone','Telefone alternativo',None),
    ('email','E-mail',None),
    ('contact_name','Pessoa de contato / responsável',None),
    ('address','Endereço (rua, número e complemento)',None),
    ('neighborhood','Bairro',None),
    ('city','Cidade',None),
    ('state','UF',STATES),
    ('postal_code','CEP',None),
    ('notes','Observações do cliente / preferência de contato',None),
]
