import tkinter as tk
from tkinter import ttk, messagebox
from .widgets import BG, NAVY, CYAN, FONT, MUTED, heading, table
from .branding import brand_header, apply_icon
from .users import Users, ROLES
from .remembered_login import RememberedLogin
from .rounded_entry import RoundedEntry


def authenticate_window(root,store):
    users=Users(store);setup=not users.has_users();result=[]
    remembered=RememberedLogin(store.path.parent)
    saved=None if setup else remembered.load()
    if saved and saved['automatic']:
        try:return users.authenticate(saved['username'],saved['password'])
        except ValueError:remembered.clear();saved=None
    win=tk.Toplevel(root);win.title('Configurar acesso' if setup else 'Entrar no OrçaPrime')
    win.geometry(f"{min(700,root.winfo_screenwidth()-40)}x{min(820 if setup else 700,root.winfo_screenheight()-90)}");win.minsize(560,480);win.configure(bg=BG);apply_icon(win)
    top=tk.Frame(win,bg=NAVY);top.pack(fill='x')
    brand_header(top,NAVY,46).pack(anchor='w',padx=24,pady=12)
    viewport=tk.Canvas(win,bg=BG,highlightthickness=0)
    scrollbar=ttk.Scrollbar(win,orient='vertical',command=viewport.yview)
    scrollbar.pack(side='right',fill='y');viewport.pack(fill='both',expand=True)
    viewport.configure(yscrollcommand=scrollbar.set)
    body=ttk.Frame(viewport,padding=(36,20))
    window_id=viewport.create_window((0,0),window=body,anchor='nw')
    body.bind('<Configure>',lambda e:viewport.configure(scrollregion=viewport.bbox('all')))
    viewport.bind('<Configure>',lambda e:viewport.itemconfigure(window_id,width=e.width))
    win.bind('<MouseWheel>',lambda e:viewport.yview_scroll(-1 if e.delta>0 else 1,'units'))
    title=tk.Frame(body,bg=BG);title.pack(anchor='w',pady=(0,8))
    tk.Label(title,text='Crie seu ' if setup else 'Bem-vindo de ',font=(FONT,26,'bold'),fg='#f3f7ff',bg=BG,padx=0).pack(side='left')
    tk.Label(title,text='acesso' if setup else 'volta',font=(FONT,26,'bold'),fg=CYAN,bg=BG,padx=0).pack(side='left')
    ttk.Label(body,text='Configure o administrador da sua assistência.' if setup else 'Entre para acessar a assistência técnica.',font=(FONT,12),style='Sub.TLabel',wraplength=580).pack(anchor='w',pady=(0,24))
    ttk.Label(body,text='Usuário').pack(anchor='w');username=tk.StringVar(value=saved['username'] if saved else '');entry=RoundedEntry(body,textvariable=username,placeholder='Digite seu usuário');entry.pack(fill='x',pady=(4,12))
    ttk.Label(body,text='Senha (mínimo 10 caracteres)' if setup else 'Senha').pack(anchor='w')
    password=tk.StringVar(value=saved['password'] if saved else '');RoundedEntry(body,textvariable=password,password=True,placeholder='Digite sua senha').pack(fill='x',pady=(4,12))
    confirmation=tk.StringVar()
    if setup:
        ttk.Label(body,text='Confirme a senha').pack(anchor='w');RoundedEntry(body,textvariable=confirmation,password=True,placeholder='Repita sua senha').pack(fill='x',pady=(4,12))
    remember=tk.BooleanVar(value=bool(saved));automatic=tk.BooleanVar(value=bool(saved and saved['automatic']))
    def remember_changed():
        if not remember.get():
            automatic.set(False);remembered.clear()
    def automatic_changed():
        if automatic.get():remember.set(True)
    ttk.Checkbutton(body,text='Salvar meus dados neste Windows',variable=remember,command=remember_changed).pack(anchor='w',pady=(6,2))
    ttk.Checkbutton(body,text='Entrar automaticamente',variable=automatic,command=automatic_changed).pack(anchor='w',pady=(2,6))
    def submit():
        try:
            if setup and password.get()!=confirmation.get():raise ValueError('As senhas não coincidem.')
            actor=users.bootstrap(username.get(),password.get()) if setup else users.authenticate(username.get(),password.get())
            if remember.get():
                try:remembered.save(username.get(),password.get(),automatic.get())
                except OSError:
                    remembered.clear();messagebox.showwarning('Salvar acesso','O acesso foi validado, mas não foi possível salvá-lo com proteção do Windows.',parent=win)
            else:remembered.clear()
            result.append(actor);password.set('');confirmation.set('');win.destroy()
        except ValueError as error:messagebox.showerror('Acesso',str(error),parent=win)
    ttk.Button(body,text='Criar administrador' if setup else 'Entrar',style='Primary.TButton',command=submit).pack(fill='x',pady=12)
    ttk.Label(body,text='Software pago — Desenvolvido por Sketch Inc. Acesso salvo protegido pelo Windows.',style='Sub.TLabel',wraplength=540).pack(anchor='w')
    win.bind('<Return>',lambda e:submit());win.bind('<Escape>',lambda e:win.destroy());entry.focus_set();win.grab_set();root.wait_window(win)
    return result[0] if result else None


class UserPages:
    def page_users(self):
        users=Users(self.store)
        heading(self.body,'Usuários e permissões','Contas locais deste computador. Apenas o administrador altera acessos.')
        toolbar=ttk.Frame(self.body);toolbar.pack(fill='x')
        tree=table(self.body,[('user','Usuário',170),('name','Nome',210),('role','Perfil',150),('active','Ativo',70)])
        rows=users.list(self.actor)
        for row in rows:tree.insert('','end',iid=str(row['id']),values=(row['username'],row['name'],row['role'],'Sim' if row['active'] else 'Não'))
        def edit(existing=None):
            data=existing or {};win=tk.Toplevel(self.root);win.title('Editar usuário' if existing else 'Criar usuário');win.geometry('540x650');win.minsize(520,650);win.configure(bg=BG);apply_icon(win)
            frame=ttk.Frame(win,padding=24);frame.pack(fill='both',expand=True);fields={}
            heading(frame,'Editar usuário' if existing else 'Novo usuário','Defina os dados de acesso e o perfil da equipe.')
            for key,label in [('username','Usuário'),('name','Nome'),('password','Nova senha (vazio mantém a atual)' if existing else 'Senha inicial — mínimo 10 caracteres')]:
                ttk.Label(frame,text=label).pack(anchor='w',pady=(8,4));fields[key]=tk.StringVar(value=data.get(key,''));RoundedEntry(frame,textvariable=fields[key],password=key=='password').pack(fill='x')
            role=tk.StringVar(value=data.get('role','ATENDIMENTO'));ttk.Label(frame,text='Perfil').pack(anchor='w',pady=(12,4));ttk.Combobox(frame,textvariable=role,values=ROLES,state='readonly').pack(fill='x')
            active=tk.BooleanVar(value=bool(data.get('active',True)));ttk.Checkbutton(frame,text='Usuário ativo',variable=active).pack(anchor='w',pady=12)
            def save():
                try:
                    users.save(self.actor,{**{k:v.get() for k,v in fields.items()},'role':role.get(),'active':active.get()},data.get('id'))
                    win.destroy();self.navigate('users')
                except ValueError as error:messagebox.showerror('Usuário',str(error),parent=win)
            ttk.Button(frame,text='Salvar',style='Primary.TButton',command=save).pack(anchor='e',pady=16);win.grab_set()
        def selected():
            if not tree.selection():raise ValueError('Selecione um usuário.')
            edit(next(r for r in rows if r['id']==int(tree.selection()[0])))
        ttk.Button(toolbar,text='+ Usuário',command=self.safe(edit)).pack(side='left')
        ttk.Button(toolbar,text='Editar / redefinir senha',command=self.safe(selected)).pack(side='left',padx=8)

    def page_fiscal(self):
        heading(self.body,'Documentos fiscais','Emissão fiscal não configurada')
        ttk.Label(self.body,text='Esta versão gera ordens de serviço, orçamentos, recibos e termos de garantia. Esses documentos não são notas fiscais autorizadas.',wraplength=760).pack(anchor='w',pady=12)
        ttk.Label(self.body,text='Para integrar a emissão de notas, é necessário definir cidade/UF, dados da empresa e o emissor utilizado. Nenhuma cobrança ou integração paga foi ativada.',wraplength=760).pack(anchor='w',pady=12)
        ttk.Label(self.body,text='Utilize o emissor fiscal autorizado da sua empresa enquanto a integração não estiver disponível.',wraplength=760,style='Sub.TLabel').pack(anchor='w',pady=12)
