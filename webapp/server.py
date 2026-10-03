"""Production entry point, with mandatory environment configuration."""
import os
import threading
from contextlib import asynccontextmanager
from urllib.parse import urlsplit
from .api import create_app
from .backup import daily_loop

def production_config(environ):
    url=environ['DATABASE_URL']
    if url.startswith('postgres://'):url=url.replace('postgres://','postgresql+psycopg://',1)
    elif url.startswith('postgresql://'):url=url.replace('postgresql://','postgresql+psycopg://',1)
    origin=(environ.get('PUBLIC_ORIGIN') or environ.get('RENDER_EXTERNAL_URL') or '').rstrip('/')
    parsed=urlsplit(origin)
    if not parsed.hostname or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
        raise ValueError('Configure PUBLIC_ORIGIN com a origem HTTPS da aplicação.')
    secure=parsed.scheme=='https'
    if not secure and not (parsed.scheme=='http' and parsed.hostname in ('127.0.0.1','localhost') and parsed.port):raise ValueError('Produção exige HTTPS.')
    if secure and not url.startswith('postgresql+psycopg://'):raise ValueError('Produção exige PostgreSQL.')
    return url,origin

def application():
    url,origin=production_config(os.environ)
    app=create_app(url,secure_cookie=origin.startswith('https://'),public_origin=origin,setup_token=os.environ.get('SETUP_TOKEN'))
    backup_dir=os.environ.get('BACKUP_DIR')
    @asynccontextmanager
    async def lifespan(app):
        stop=threading.Event();worker=None
        if backup_dir:
            worker=threading.Thread(target=daily_loop,args=(app.state.engine,backup_dir,stop),daemon=True);worker.start()
        yield
        stop.set()
        if worker:worker.join(timeout=5)
        app.state.engine.dispose()
    app.router.lifespan_context=lifespan
    return app
