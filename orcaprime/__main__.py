import os
import sys
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from .storage import Store
from .ui import App
from .user_ui import authenticate_window
from .maintenance import run_daily_backup
from .client_configuration import configured_client
from .widgets import styles

def main():
    if '--backup-only' in sys.argv:
        from .backup_scheduler import backup_job
        try:backup_job()
        except Exception:return 1
        return 0
    if sys.platform=='win32':
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('OliverTech.OrcaPrime.Premium')
    root=tk.Tk()
    root.report_callback_exception=lambda kind,value,trace:messagebox.showerror('OrçaPrime','Não foi possível concluir a operação. Verifique os dados e tente novamente.',parent=root)
    base=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent.parent))
    data=Path(os.environ.get('LOCALAPPDATA',Path.home()/'.local'/'share'))/'OrcaPrime'
    try:root.iconbitmap(str(base/'assets'/'orcaprime-commercial.ico'))
    except tk.TclError:pass
    store=Store(data/'orcaprime.db')
    try:
        backup=run_daily_backup(store)
        if backup.cloud_error:messagebox.showwarning('Backup automático','Backup local salvo. Não foi possível copiar para a segunda pasta: '+backup.cloud_error,parent=root)
    except (OSError,ValueError) as error: messagebox.showwarning('Backup automático','Não foi possível criar a cópia automática. Confira o espaço e as permissões da pasta de dados.',parent=root)
    styles(root);root.withdraw()
    try:license_client=configured_client(base,data)
    except ValueError as error:
        messagebox.showerror('Licenciamento',str(error),parent=root);root.destroy();return 1
    actor=authenticate_window(root,store)
    if actor is None:
        root.destroy();return
    root.deiconify()
    app=App(root,store,license_client=license_client,actor=actor)
    root.mainloop()

if __name__=='__main__':sys.exit(main() or 0)
