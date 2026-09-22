import tkinter as tk
from tkinter import ttk, messagebox

NAVY='#10233f';TEAL='#087f78';BG='#f2f5f9';TEXT='#172b45';MUTED='#64748b'

def styles(root):
    root.configure(bg=BG);root.option_add('*Font',('Segoe UI',10))
    s=ttk.Style(root);s.theme_use('clam')
    s.configure('.',font=('Segoe UI',10),background=BG,foreground=TEXT)
    s.configure('TFrame',background=BG);s.configure('Card.TFrame',background='white')
    s.configure('TLabel',background=BG);s.configure('Title.TLabel',font=('Segoe UI',24,'bold'))
    s.configure('Sub.TLabel',foreground=MUTED)
    s.configure('TButton',padding=(14,9),background='#e2e8f0',borderwidth=0)
    s.map('TButton',background=[('active','#cbd5e1')])
    s.configure('Primary.TButton',background=TEAL,foreground='white')
    s.map('Primary.TButton',background=[('active','#065f59'),('disabled','#94a3b8')],foreground=[('disabled','#f1f5f9')])
    s.configure('TEntry',padding=7,fieldbackground='white',foreground=TEXT)
    s.configure('TCombobox',padding=7,fieldbackground='white',foreground=TEXT)
    s.map('TCombobox',fieldbackground=[('readonly','white')],foreground=[('readonly',TEXT)])
    s.configure('Treeview',rowheight=34,background='white',fieldbackground='white',foreground=TEXT,borderwidth=0)
    s.configure('Treeview.Heading',background='#e2e8f0',foreground=TEXT,font=('Segoe UI',10,'bold'),padding=10)
    s.map('Treeview',background=[('selected',TEAL)],foreground=[('selected','white')])

def heading(parent,title,subtitle=''):
    ttk.Label(parent,text=title,style='Title.TLabel').pack(anchor='w',pady=(0,5))
    if subtitle: ttk.Label(parent,text=subtitle,style='Sub.TLabel',wraplength=850).pack(anchor='w',pady=(0,20))

def table(parent,columns):
    frame=ttk.Frame(parent);frame.pack(fill='both',expand=True,pady=12)
    tree=ttk.Treeview(frame,columns=[c[0] for c in columns],show='headings',selectmode='browse',height=8)
    for key,label,width in columns:
        tree.heading(key,text=label);tree.column(key,width=width,minwidth=65)
    sy=ttk.Scrollbar(frame,orient='vertical',command=tree.yview);sx=ttk.Scrollbar(frame,orient='horizontal',command=tree.xview)
    tree.configure(yscrollcommand=sy.set,xscrollcommand=sx.set)
    tree.grid(row=0,column=0,sticky='nsew');sy.grid(row=0,column=1,sticky='ns');sx.grid(row=1,column=0,sticky='ew')
    frame.rowconfigure(0,weight=1);frame.columnconfigure(0,weight=1)
    return tree

class Form(tk.Toplevel):
    def __init__(self,parent,title,fields,data,on_save,guard):
        super().__init__(parent);self.title(title);self.transient(parent);self.configure(bg=BG)
        self.resizable(True,True);self.minsize(460,350);self.vars={};self.guard=guard
        body=ttk.Frame(self,padding=24);body.pack(fill='both',expand=True);heading(body,title)
        for key,label,options in fields:
            ttk.Label(body,text=label).pack(anchor='w',pady=(8,3))
            var=tk.StringVar(value=data.get(key,''));self.vars[key]=var
            widget=ttk.Combobox(body,textvariable=var,values=options,state='readonly') if options else ttk.Entry(body,textvariable=var)
            widget.pack(fill='x')
        def save():
            try: guard();on_save({k:v.get() for k,v in self.vars.items()});self.destroy()
            except (ValueError,OSError) as e: messagebox.showerror('Confira os dados',str(e),parent=self)
        ttk.Button(body,text='Salvar',style='Primary.TButton',command=save).pack(anchor='e',pady=(20,0))
        self.bind('<Escape>',lambda e:self.destroy());self.grab_set();self.focus_set()
