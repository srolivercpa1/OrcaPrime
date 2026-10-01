"""Run with python -m webapp.cli; secrets are prompted, never command arguments."""
import argparse
import getpass
import os
from .security import bootstrap
from .backup import backup,restore
from .db import database

def main():
    p=argparse.ArgumentParser(description='Administração OrçaPrime Web')
    p.add_argument('action',choices=['init','backup','restore'])
    p.add_argument('--file');p.add_argument('--directory',default='backup')
    args=p.parse_args();url=os.environ['DATABASE_URL']
    if url.startswith(('postgres://','postgresql://')):url='postgresql+psycopg://'+url.split('://',1)[1]
    if args.action=='init':
        email=input('E-mail do proprietário: ').strip();password=getpass.getpass('Senha (mínimo 12 caracteres): ')
        if password!=getpass.getpass('Confirme a senha: '):raise SystemExit('As senhas não conferem.')
        bootstrap(url,email,password);print('Proprietário criado. Entre pelo navegador.')
    elif args.action=='backup':
        engine,_=database(url)
        try:print(backup(engine,args.directory))
        finally:engine.dispose()
    else:
        if not args.file:raise SystemExit('Informe --file com o backup a restaurar em banco vazio.')
        restore(url,args.file);print('Backup restaurado. Sessões antigas não foram restauradas.')
if __name__=='__main__':main()
