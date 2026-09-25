import os
import sys
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from .storage import Store
from .ui import App
from .user_ui import authenticate_window
from .maintenance import daily_backup
from .widgets import styles

def main():
    if sys.platform=='win32':
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('OliverTech.OrcaPrime.Premium')
    root=tk.Tk()
    root.report_callback_exception=lambda kind,value,trace:messagebox.showerror('OrçaPrime','Não foi possível concluir a operação. Verifique os dados e tente novamente.',parent=root)
    base=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent.parent))
    data=Path(os.environ.get('LOCALAPPDATA',Path.home()/'.local'/'share'))/'OrcaPrime'
    try:root.iconbitmap(str(base/'assets'/'orcaprime-premium-r2.ico'))
    except tk.TclError:pass
    store=Store(data/'orcaprime.db')
    try: daily_backup(store)
    except (OSError,ValueError) as error: messagebox.showwarning('Backup automático','Não foi possível criar a cópia automática. Confira o espaço e as permissões da pasta de dados.',parent=root)
    styles(root);root.withdraw()
    actor=authenticate_window(root,store)
    if actor is None:
        root.destroy();return
    root.deiconify()
    app=App(root,store,actor=actor)
    root.mainloop()

if __name__=='__main__':main()
