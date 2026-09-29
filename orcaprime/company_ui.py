"""Persistent company logo controls shared by all service documents."""
import io
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from .company_logo import logo_bytes


def logo_controls(app,body):
    frame=ttk.LabelFrame(body,text='Logo da empresa',padding=12);frame.pack(fill='x',pady=(0,12))
    preview=ttk.Label(frame);preview.pack(anchor='w')
    ttk.Label(frame,text='Salva automaticamente. Será impressa nas OS e garantias, inclusive nas já cadastradas.',wraplength=480).pack(anchor='w',pady=6)
    bar=ttk.Frame(frame);bar.pack(fill='x')
    def refresh():
        encoded=app.store.company_logo()
        if encoded:
            with Image.open(io.BytesIO(logo_bytes(encoded))) as source:
                source.thumbnail((240,90));preview.image=ImageTk.PhotoImage(source.copy(),master=app.root)
            preview.configure(image=preview.image,text='')
        else:preview.configure(image='',text='Nenhuma logo cadastrada');preview.image=None
    def choose():
        path=filedialog.askopenfilename(parent=app.root,title='Escolher logo da empresa',filetypes=[('Imagens','*.png *.jpg *.jpeg *.webp')])
        if path:
            app.guard();app.store.save_company_logo(path);refresh()
    def remove():
        if messagebox.askyesno('Remover logo','Remover a logo das próximas impressões?',parent=app.root):
            app.guard();app.store.save_company_logo(None);refresh()
    ttk.Button(bar,text='Adicionar / trocar logo',command=app.safe(choose)).pack(side='left')
    ttk.Button(bar,text='Remover logo',command=app.safe(remove)).pack(side='left',padx=8)
    refresh()
