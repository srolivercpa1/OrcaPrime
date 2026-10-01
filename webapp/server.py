"""Production entry point, with mandatory environment configuration."""
import os
import threading
from contextlib import asynccontextmanager
from .api import create_app
from .backup import daily_loop

def application():
    url=os.environ['DATABASE_URL']
    if url.startswith('postgres://'):url=url.replace('postgres://','postgresql+psycopg://',1)
    elif url.startswith('postgresql://'):url=url.replace('postgresql://','postgresql+psycopg://',1)
    origin=os.environ['PUBLIC_ORIGIN'].rstrip('/')
    secure=origin.startswith('https://')
    if not secure and not origin.startswith(('http://127.0.0.1:','http://localhost:')):raise ValueError('Produção exige HTTPS.')
    if secure and not url.startswith('postgresql+psycopg://'):raise ValueError('Produção exige PostgreSQL.')
    app=create_app(url,secure_cookie=secure,public_origin=origin)
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
