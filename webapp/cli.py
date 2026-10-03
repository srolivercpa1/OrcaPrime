"""Run with python -m webapp.cli; secrets are prompted, never command arguments."""
import argparse
import getpass
import os
from .security import bootstrap
from .backup import backup,restore
from sqlalchemy import create_engine

def main():
    p=argparse.ArgumentParser(description='Administração OrçaPrime Web')
    p.add_argument('action',choices=['init','backup','restore'])
    p.add_argument('--file');p.add_argument('--directory',default='backup')
    p.add_argument('--encrypted',action='store_true',help='Criptografar backup com BACKUP_ENCRYPTION_KEY (obrigatória).')
    args=p.parse_args();url=os.environ['DATABASE_URL']
    if url.startswith(('postgres://','postgresql://')):url='postgresql+psycopg://'+url.split('://',1)[1]
    if args.action=='init':
        email=input('E-mail do proprietário: ').strip();password=getpass.getpass('Senha (mínimo 12 caracteres): ')
        if password!=getpass.getpass('Confirme a senha: '):raise SystemExit('As senhas não conferem.')
        bootstrap(url,email,password);print('Proprietário criado. Entre pelo navegador.')
    elif args.action=='backup':
        key=os.environ.get('BACKUP_ENCRYPTION_KEY') if args.encrypted else None
        if args.encrypted and not key:raise SystemExit('Configure BACKUP_ENCRYPTION_KEY antes do backup criptografado.')
        # Do not initialize schema: cloud backup credentials need SELECT only.
        engine=create_engine(url,pool_pre_ping=True)
        try:print(backup(engine,args.directory,encryption_key=key))
        finally:engine.dispose()
    else:
        if not args.file:raise SystemExit('Informe --file com o backup a restaurar em banco vazio.')
        restore(url,args.file,encryption_key=os.environ.get('BACKUP_ENCRYPTION_KEY'));print('Backup restaurado. Sessões antigas não foram restauradas.')
if __name__=='__main__':main()
