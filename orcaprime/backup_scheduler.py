"""Headless entry point for Windows Task Scheduler."""
import os
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .maintenance import run_daily_backup
from .storage import Store


def read_backup_status(data_dir):
    try:
        value=json.loads((Path(data_dir)/'backup-scheduler-status.json').read_text(encoding='utf-8'))
        return value if isinstance(value,dict) else {}
    except (OSError,ValueError):return {}


def _write_backup_status(data,state,error='',local_path=''):
    data.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.backup-scheduler-status-',suffix='.tmp',dir=data)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            json.dump({'state':state,'at':datetime.now(timezone.utc).isoformat(),
                       'error':error,'local_path':str(local_path)},stream,ensure_ascii=False)
        os.replace(name,data/'backup-scheduler-status.json')
    finally:Path(name).unlink(missing_ok=True)


def backup_job(data_dir=None):
    data=Path(data_dir) if data_dir is not None else Path(os.environ.get('LOCALAPPDATA',Path.home()/'.local'/'share'))/'OrcaPrime'
    partial=False
    try:
        if not (data/'orcaprime.db').is_file():
            raise FileNotFoundError('Banco OrçaPrime ainda não existe: '+str(data/'orcaprime.db'))
        result=run_daily_backup(Store(data/'orcaprime.db'),force=True)
        if result.cloud_error:
            error='Backup local salvo em '+str(result.local_path)+'; segunda pasta falhou: '+result.cloud_error
            _write_backup_status(data,'partial',error,result.local_path)
            partial=True
            raise RuntimeError(error)
        _write_backup_status(data,'ok',local_path=result.local_path)
        return result
    except Exception as error:
        if not partial:
            _write_backup_status(data,'error',str(error))
        raise
