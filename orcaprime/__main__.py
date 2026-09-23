import os
import sys
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from .storage import Store
from .ui import App

def main():
    root=tk.Tk()
    root.report_callback_exception=lambda kind,value,trace:messagebox.showerror('OrçaPrime','Não foi possível concluir a operação. Verifique os dados e tente novamente.',parent=root)
    base=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent.parent))
    data=Path(os.environ.get('LOCALAPPDATA',Path.home()/'.local'/'share'))/'OrcaPrime'
    try:root.iconbitmap(str(base/'assets'/'orcaprime.ico'))
    except tk.TclError:pass
    app=App(root,Store(data/'orcaprime.db'))
    root.mainloop()

if __name__=='__main__':main()
