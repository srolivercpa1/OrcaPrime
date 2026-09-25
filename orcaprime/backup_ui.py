"""Backup settings and restore controls for the desktop application."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from .maintenance import backup_settings, save_backup_settings, run_daily_backup, restore_backup, default_backup_dir
from .backup_scheduler import read_backup_status
from .widgets import heading


class BackupPages:
    def page_backup(self):
        heading(self.body,'Proteja seus dados','Cópia diária compactada, com uma segunda pasta opcional.')
        settings=backup_settings(self.store)
        ttk.Label(self.body,text='Pasta local: '+str(default_backup_dir(self.store)),wraplength=760).pack(anchor='w',pady=(20,12))
        status=read_backup_status(self.store.path.parent)
        if status:
            detail=status.get('error') or ('Cópia salva em '+status.get('local_path',''))
            ttk.Label(self.body,text='Última execução agendada: '+status.get('at','')+' — '+detail,wraplength=760,
                      foreground='#ffad56' if status.get('error') else '#51c58a').pack(anchor='w',pady=(0,12))
        ttk.Label(self.body,text='Versões diárias a manter (1 a 365)').pack(anchor='w')
        retention=tk.StringVar(value=str(settings['retention']))
        ttk.Entry(self.body,textvariable=retention,width=8).pack(anchor='w',pady=(3,12))
        ttk.Label(self.body,text='Segunda pasta sincronizada (opcional)').pack(anchor='w')
        folder=tk.StringVar(value=settings['cloud_folder'])
        row=ttk.Frame(self.body);row.pack(fill='x',pady=(3,12))
        ttk.Entry(row,textvariable=folder).pack(side='left',fill='x',expand=True)
        ttk.Button(row,text='Escolher pasta',command=lambda:folder.set(filedialog.askdirectory(parent=self.root) or folder.get())).pack(side='left',padx=(8,0))
        ttk.Label(self.body,text='Sincronize apenas os ZIPs da segunda pasta. O banco em uso permanece no computador.',wraplength=760).pack(anchor='w',pady=(0,12))

        def save():
            save_backup_settings(self.store,int(retention.get()),folder.get())
            messagebox.showinfo('Backup','Configurações salvas.',parent=self.root)

        def backup():
            save_backup_settings(self.store,int(retention.get()),folder.get())
            result=run_daily_backup(self.store,force=True)
            if result.cloud_error:
                messagebox.showwarning('Backup','Cópia local salva em '+str(result.local_path)+'\nA segunda pasta falhou: '+result.cloud_error,parent=self.root)
            else:messagebox.showinfo('Backup','Cópia salva em '+str(result.local_path),parent=self.root)

        def restore():
            path=filedialog.askopenfilename(parent=self.root,filetypes=[('Backup OrçaPrime','*.zip *.db')])
            if path and messagebox.askyesno('Restaurar backup','Substituir os dados atuais? Uma cópia prévia será preservada automaticamente.',parent=self.root):
                restore_backup(self.store,path)
                messagebox.showinfo('Restauração','Backup restaurado. Abra o programa novamente para entrar com os usuários restaurados.',parent=self.root)
                self.closed=True;self.root.destroy()

        ttk.Button(self.body,text='Salvar configurações',command=self.safe(save)).pack(anchor='w',pady=8)
        ttk.Button(self.body,text='Criar backup agora',style='Primary.TButton',command=self.safe(backup)).pack(anchor='w',pady=8)
        ttk.Button(self.body,text='Restaurar ZIP ou DB antigo',command=self.safe(restore)).pack(anchor='w',pady=8)
