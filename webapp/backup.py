"""Compressed, consistent snapshots. Restore only into an empty web database."""
import base64
import gzip
import io
import json
import os
import time
from datetime import datetime,timezone
from pathlib import Path
from sqlalchemy import select
from cryptography.fernet import Fernet, InvalidToken
from .db import Base,database

TABLES=[t for t in Base.metadata.sorted_tables if t.name!='web_sessions']
MAX_RESTORE_BYTES=512*1024*1024

def backup(engine,directory,keep=14,encryption_key=None):
    cipher=Fernet(encryption_key) if encryption_key is not None else None
    folder=Path(directory);folder.mkdir(parents=True,exist_ok=True,mode=0o700)
    extension='.json.gz.enc' if cipher else '.json.gz'
    target=folder/('orcaprime-web-'+datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')+extension)
    with engine.connect() as connection:
        if engine.dialect.name=='postgresql':connection=connection.execution_options(isolation_level='REPEATABLE READ')
        with connection.begin():
            data={t.name:[dict(row) for row in connection.execute(select(t)).mappings()] for t in TABLES}
    for photo in data.get('web_photos',[]):photo['content']=base64.b64encode(photo['content']).decode()
    raw=json.dumps({'format':'OrcaPrime-Web-1','tables':data},ensure_ascii=False).encode()
    if len(raw)>MAX_RESTORE_BYTES:raise ValueError('Backup acima do limite de restauração de 512 MiB.')
    compressed=gzip.compress(raw,compresslevel=6)
    payload=cipher.encrypt(compressed) if cipher else compressed
    temp=target.with_suffix('.tmp')
    with os.fdopen(os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600),'wb') as f:
        f.write(payload);f.flush();os.fsync(f.fileno())
    temp.replace(target)
    for old in sorted(folder.glob('orcaprime-web-*'+extension),reverse=True)[max(1,keep):]:old.unlink()
    return target

def restore(url,path,encryption_key=None):
    source=path
    if str(path).endswith('.enc'):
        if not encryption_key:raise ValueError('Informe BACKUP_ENCRYPTION_KEY para restaurar o backup criptografado.')
        try:source=io.BytesIO(Fernet(encryption_key).decrypt(Path(path).read_bytes()))
        except (InvalidToken,ValueError):raise ValueError('Chave incorreta ou backup criptografado danificado.') from None
    with gzip.open(source,'rb') as f:
        raw=f.read(MAX_RESTORE_BYTES+1)
        if len(raw)>MAX_RESTORE_BYTES:raise ValueError('Backup acima do limite de restauração.')
        data=json.loads(raw)
    if data.get('format')!='OrcaPrime-Web-1':raise ValueError('Formato de backup inválido.')
    if set(data['tables'])!={t.name for t in TABLES}:raise ValueError('Tabelas do backup incompatíveis.')
    engine,_=database(url)
    try:
        with engine.begin() as conn:
            if any(conn.execute(select(t).limit(1)).first() for t in Base.metadata.sorted_tables):raise ValueError('Restaure apenas em banco vazio.')
            for table in TABLES:
                rows=data['tables'][table.name]
                if table.name=='web_photos':
                    for row in rows:row['content']=base64.b64decode(row['content'],validate=True)
                if rows:conn.execute(table.insert(),rows)
    finally:engine.dispose()

def daily_loop(engine,directory,stop):
    """Run once per UTC day; keep backups private and retry failed runs."""
    import logging
    while not stop.is_set():
        day=datetime.now(timezone.utc).strftime('%Y%m%d')
        if not list(Path(directory).glob('orcaprime-web-'+day+'-*.json.gz')):
            try:backup(engine,directory)
            except Exception:logging.getLogger(__name__).exception('Falha no backup diário; nova tentativa em 60 segundos.')
        stop.wait(60)
