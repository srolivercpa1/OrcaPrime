from .widgets import FONT
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from pathlib import Path
from .domain import brl,decimal_text,STATUSES
from .license_client import format_code,LicenseFailure
from .widgets import NAVY,TEAL,BG,MUTED,styles,heading,table,Form
from .quote_editor import QuoteEditor
from .pdf import export_quote
from .workshop_ui import WorkshopPages
from .workshop import Workshop
from .dashboard_ui import DashboardPages
from .user_ui import UserPages
from . import __version__

class App(DashboardPages, WorkshopPages, UserPages):
    def __init__(self,root,store,license_client=None,auto_start=True,actor=None):
        self.actor=actor or {'id':0,'name':'Local','role':'ADMIN'};self.current_page=None
        self.workshop=Workshop(store,self.actor)
        self.root=root;self.store=store;self.license=license_client;self.events=queue.Queue();self.main_visible=False
        self.closed=False;self.generation=0;self.suspended=[];self.hidden_dialogs=[];self.activation_host=None;root.title('OrçaPrime | Gestão Profissional de Assistência')
        root.geometry('1180x790');root.minsize(920,650);styles(root)
        root.protocol('WM_DELETE_WINDOW',self.close);root.after(100,self.poll)
        if auto_start: self.show_activation()
    def close(self):
        if any(isinstance(w,tk.Toplevel) for w in self.root.winfo_children()):
            if not messagebox.askyesno('Fechar OrçaPrime','Há uma edição aberta. Encerrar e descartar as alterações não salvas?',parent=self.root):return
        self.closed=True;self.root.destroy()
    def poll(self):
        if self.closed:return
        try:
            while True:
                callback,result,error=self.events.get_nowait()
                try:callback(result,error)
                except Exception as exc:self.root.report_callback_exception(type(exc),exc,exc.__traceback__)
        except queue.Empty: pass
        finally:
            if not self.closed:self.root.after(100,self.poll)
    def async_call(self,work,callback):
        def run():
            try: result=work();error=None
            except Exception as e: result=None;error=e
            self.events.put((callback,result,error))
        threading.Thread(target=run,daemon=True).start()
    def clear(self):
        for child in self.root.winfo_children(): child.destroy()
    def show_activation(self,notice=''):
        if self.license is None:
            self.show_main();return
        if self.main_visible:
            self.suspended=[];self.hidden_dialogs=[]
            for child in self.root.winfo_children():
                if isinstance(child,tk.Toplevel):
                    try:child.grab_release()
                    except tk.TclError:pass
                    child.withdraw();self.hidden_dialogs.append(child)
                elif child.winfo_manager()=='pack':
                    self.suspended.append((child,child.pack_info()));child.pack_forget()
        elif self.activation_host and self.activation_host.winfo_exists():
            self.activation_host.destroy()
        else:self.clear()
        self.main_visible=False;self.generation+=1;generation=self.generation
        host=ttk.Frame(self.root);host.pack(fill='both',expand=True);self.activation_host=host
        top=tk.Frame(host,bg=NAVY,height=170);top.pack(fill='x');top.pack_propagate(False)
        tk.Label(top,text='OrçaPrime',bg=NAVY,fg='white',font=(FONT,34,'bold')).pack(pady=(30,4))
        tk.Label(top,text='SISTEMA PROFISSIONAL DE ORÇAMENTOS',bg=NAVY,fg='#9bded4',font=(FONT,11)).pack()
        box=ttk.Frame(host,padding=35);box.pack(expand=True)
        heading(box,'ATIVAÇÃO DO ORÇAPRIME','Insira o código recebido para ativar este computador.')
        ttk.Label(box,text='Código de ativação').pack(anchor='w')
        code=tk.StringVar();entry=ttk.Entry(box,textvariable=code,width=35,font=('Consolas',17));entry.pack(fill='x',pady=10)
        changing=False
        def format_value(*_):
            nonlocal changing
            if changing:return
            changing=True;raw=format_code(code.get());code.set(raw);changing=False
        code.trace_add('write',format_value)
        controls=ttk.Frame(box);controls.pack(fill='x')
        def paste():
            try: code.set(self.root.clipboard_get())
            except tk.TclError: pass
        ttk.Button(controls,text='Colar código',command=paste).pack(side='left')
        state=ttk.Label(box,text=notice,wraplength=490,foreground='#a33718');state.pack(fill='x',pady=15)
        buttons=[]
        def finish(result,error):
            if generation!=self.generation or self.closed:return
            if error:
                state.configure(text=str(error));[b.configure(state='normal') for b in buttons]
            else: code.set('');self.show_main()
        def start(work):
            [b.configure(state='disabled') for b in buttons];state.configure(text='Validando licença…')
            self.async_call(work,finish)
        def activate():
            if not self.license: state.configure(text='Configuração de licenciamento ausente. Solicite ao fornecedor um instalador configurado.');return
            value=code.get();start(lambda:self.license.activate(value))
        button=ttk.Button(controls,text='ATIVAR',style='Primary.TButton',command=activate);button.pack(side='right');buttons.append(button)
        if self.license and self.license.token:
            retry=ttk.Button(box,text='Validar ativação existente',command=lambda:start(self.license.validate));retry.pack(fill='x');buttons.append(retry)
            if not notice:start(self.license.validate)
        ttk.Label(box,text='Licença individual | Validação segura pela internet',style='Sub.TLabel').pack(pady=20)
        ttk.Label(host,text='Desenvolvido por OLIVERTECH SOLUÇÕES',style='Sub.TLabel').pack(pady=20)
        entry.focus_set()
    def allowed_pages(self):
        common={'orders','warranties','license'}
        role=self.actor['role']
        if role=='TECNICO':return common
        pages=common|{'dashboard','customers','quotes','catalog','printers','fiscal'}
        if role in ('FINANCEIRO','ADMIN'):pages|={'stock','suppliers','finance','reports'}
        if role=='ADMIN':pages|={'company','backup','users'}
        return pages
    def guard(self):
        if self.actor.get('id'):
            with self.store.connect() as db:
                user=db.execute('SELECT role,active FROM app_users WHERE id=?',(self.actor['id'],)).fetchone()
            if not user or not user[1]:raise ValueError('Seu acesso foi desativado. Feche o programa.')
            self.actor['role']=user[0]
        if self.current_page and self.current_page not in self.allowed_pages():raise ValueError('Seu perfil não permite esta operação.')
        if self.license is not None and not self.license.allowed(): raise ValueError('Sua licença precisa ser validada. Salve seu trabalho antes de encerrar a sessão.')
    def safe(self,action):
        def run():
            try: self.guard();action()
            except (ValueError,OSError,RuntimeError,PermissionError) as e: messagebox.showerror('OrçaPrime',str(e),parent=self.root)
        return run
    def show_main(self):
        self.guard()
        if self.suspended:
            if self.activation_host:self.activation_host.destroy();self.activation_host=None
            for widget,options in self.suspended:widget.pack(**options)
            self.suspended=[]
            for dialog in self.hidden_dialogs:
                if dialog.winfo_exists():dialog.deiconify();dialog.grab_set()
            self.hidden_dialogs=[];self.main_visible=True;self.generation+=1
            generation=self.generation
            if self.license is not None:
                self.root.after(1000,lambda:self.watch(generation));self.root.after(300000,lambda:self.revalidate(generation))
            return
        self.clear();self.activation_host=None;self.main_visible=True;self.generation+=1
        nav=tk.Frame(self.root,bg=NAVY,width=222);nav.pack(side='left',fill='y');nav.pack_propagate(False)
        tk.Label(nav,text='OrçaPrime',bg=NAVY,fg='white',font=(FONT,23,'bold')).pack(anchor='w',padx=22,pady=(24,3))
        tk.Label(nav,text='GESTÃO DA ASSISTÊNCIA',bg=NAVY,fg='#87a5c5',font=(FONT,8)).pack(anchor='w',padx=22,pady=(0,16))
        canvas=tk.Canvas(nav,bg=NAVY,highlightthickness=0);scroll=ttk.Scrollbar(nav,orient='vertical',command=canvas.yview)
        scroll.pack(side='right',fill='y');canvas.pack(fill='both',expand=True);canvas.configure(yscrollcommand=scroll.set)
        menu=tk.Frame(canvas,bg=NAVY);win=canvas.create_window((0,0),window=menu,anchor='nw')
        menu.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')));canvas.bind('<Configure>',lambda e:canvas.itemconfigure(win,width=e.width))
        self.nav_buttons={}
        for key,label in [('dashboard','Visão geral'),('orders','Ordens de serviço'),('customers','Clientes'),('quotes','Orçamentos'),('catalog','Produtos e serviços'),('stock','Estoque e peças'),('suppliers','Fornecedores'),('finance','Financeiro e caixa'),('warranties','Garantias e retornos'),('reports','Relatórios'),('printers','Impressoras'),('fiscal','Notas fiscais'),('users','Usuários'),('company','Minha empresa'),('backup','Backup e restauração'),('license','Sobre o OrçaPrime' if self.license is None else 'Minha licença')]:
            if key not in self.allowed_pages():continue
            section={'dashboard':'ATENDIMENTO','stock':'GESTÃO','users':'CONFIGURAÇÕES'}.get(key)
            if section:tk.Label(menu,text=section,bg=NAVY,fg='#91a7c2',font=(FONT,8,'bold'),anchor='w').pack(fill='x',padx=22,pady=(14,6))
            b=tk.Button(menu,text=label,anchor='w',bg=NAVY,fg='#d7e3f3',activebackground=TEAL,activeforeground='white',relief='flat',bd=0,highlightthickness=1,highlightbackground=NAVY,highlightcolor=TEAL,padx=16,pady=8,font=(FONT,10),cursor='hand2',command=self.safe(lambda k=key:self.navigate(k)))
            b.pack(fill='x',padx=12,pady=2);self.nav_buttons[key]=b
        tk.Label(nav,text='OLIVERTECH SOLUÇÕES\nv'+__version__,bg=NAVY,fg='#87a5c5',font=(FONT,9),justify='left').pack(anchor='w',padx=22,pady=22)
        main=ttk.Frame(self.root);main.pack(side='left',fill='both',expand=True)
        header=ttk.Frame(main,padding=(28,16),style='Header.TFrame');header.pack(fill='x')
        ttk.Label(header,text=self.store.company().get('name') or 'Bem-vindo ao OrçaPrime',font=(FONT,11,'bold'),wraplength=340,style='Header.TLabel').pack(side='left')
        ttk.Label(header,text=(self.actor.get('name','Local')+' | Offline') if self.license is None else '● Licença '+self.license.payload['plan'],foreground=TEAL,style='Header.TLabel').pack(side='right')
        ttk.Separator(main).pack(fill='x');self.body=ttk.Frame(main,padding=28);self.body.pack(fill='both',expand=True)
        self.navigate('dashboard' if 'dashboard' in self.allowed_pages() else 'orders');generation=self.generation
        if self.license is not None:
            self.root.after(1000,lambda:self.watch(generation));self.root.after(300000,lambda:self.revalidate(generation))
    def watch(self,generation):
        if self.license is None or not self.main_visible or generation!=self.generation:return
        if not self.license.allowed():
            self.show_activation('A validação expirou. Conecte-se à internet para continuar.');return
        self.root.after(1000,lambda:self.watch(generation))
    def revalidate(self,generation):
        if self.license is None or not self.main_visible or generation!=self.generation:return
        def done(result,error):
            if generation!=self.generation:return
            if error and (not isinstance(error,LicenseFailure) or not error.network): self.show_activation(str(error));return
            self.root.after(300000,lambda:self.revalidate(generation))
        self.async_call(self.license.validate,done)
    def navigate(self,page):
        if page not in self.allowed_pages():raise ValueError('Seu perfil não permite acessar esta área.')
        self.current_page=page
        self.guard()
        for widget in self.body.winfo_children(): widget.destroy()
        for key,b in self.nav_buttons.items(): b.configure(bg='#183a49' if key==page else NAVY,fg='#7ce4ce' if key==page else '#d7e3f3')
        getattr(self,'page_'+page)()
    def page_customers(self): self.records(False)
    def page_catalog(self): self.records(True)
    def records(self,catalog):
        title='Produtos e serviços' if catalog else 'Clientes';heading(self.body,title,'Cadastre e mantenha suas informações sempre à mão.')
        bar=ttk.Frame(self.body);bar.pack(fill='x');search=tk.StringVar();ttk.Entry(bar,textvariable=search,width=35).pack(side='left')
        cols=[('name','Descrição' if catalog else 'Nome',260),('one','Tipo' if catalog else 'Documento',150),('two','Unidade' if catalog else 'Telefone',130),('three','Preço' if catalog else 'E-mail',180)]
        tree=table(self.body,cols);data=[]
        def refresh(*_):
            nonlocal data
            data=self.store.list_items() if catalog else self.store.list_customers();tree.delete(*tree.get_children())
            for d in data:
                if search.get().casefold() not in str(d).casefold():continue
                vals=(d['description'],d['kind'],d['unit'],brl(d['price_cents'])) if catalog else (d['name'],d['document'],d['phone'],d['email'])
                tree.insert('','end',iid=str(d['id']),values=vals)
        def edit(new=False):
            selected=tree.selection();record={} if new else next((d for d in data if selected and str(d['id'])==selected[0]),None)
            if record is None: raise ValueError('Selecione um registro para editar.')
            if catalog:
                fields=[('description','Descrição *',None),('kind','Tipo',('PRODUTO','SERVIÇO')),('unit','Unidade',None),('price','Preço (R$) *',None)]
                values=dict(record,price=decimal_text(record.get('price_cents',0)),kind=record.get('kind','SERVIÇO'),unit=record.get('unit','un'))
            else:
                fields=[('name','Nome *',None),('document','CPF / CNPJ',None),('phone','Telefone',None),('email','E-mail',None),('address','Endereço',None)];values=record
            def save(d):
                (self.store.save_item if catalog else self.store.save_customer)(d,record.get('id'));refresh()
            Form(self.root,('Novo ' if new else 'Editar ')+('item' if catalog else 'cliente'),fields,values,save,self.guard)
        ttk.Button(bar,text='Editar selecionado',command=self.safe(edit)).pack(side='right',padx=8)
        ttk.Button(bar,text='+ Novo',style='Primary.TButton',command=self.safe(lambda:edit(True))).pack(side='right')
        tree.bind('<Double-1>',lambda e:self.safe(edit)());search.trace_add('write',refresh);refresh()
    def new_quote(self,quote=None,duplicate=False):
        if not self.store.list_customers(): messagebox.showinfo('Primeiro cliente','Cadastre um cliente antes de criar o orçamento.');self.navigate('customers');return
        QuoteEditor(self.root,self.store,self.guard,lambda:self.navigate('quotes'),quote,duplicate)
    def page_quotes(self):
        heading(self.body,'Orçamentos','Crie, acompanhe e exporte suas propostas em PDF.')
        bar=ttk.Frame(self.body);bar.pack(fill='x');search=tk.StringVar();ttk.Entry(bar,textvariable=search,width=38).pack(side='left')
        ttk.Label(bar,text='Busca por número, cliente ou situação',style='Sub.TLabel').pack(side='left',padx=10)
        ttk.Button(bar,text='+ Novo',style='Primary.TButton',command=self.safe(self.new_quote)).pack(side='right')
        tree=table(self.body,[('n','Número',125),('c','Cliente',250),('v','Validade',110),('s','Situação',120),('t','Total',130)])
        def refresh(*_):
            tree.delete(*tree.get_children())
            for q in self.store.list_quotes(search.get()): tree.insert('','end',iid=str(q['id']),values=(q['number'],q['customer']['name'],'/'.join(q['valid_until'].split('-')[::-1]),q['status'],brl(q['total_cents'])))
        def selected():
            sel=tree.selection()
            if not sel:raise ValueError('Selecione um orçamento.')
            return self.store.get_quote(int(sel[0]))
        def pdf():
            q=selected();path=filedialog.asksaveasfilename(parent=self.root,defaultextension='.pdf',initialfile='Orcamento-'+q['number']+'.pdf',filetypes=[('PDF','*.pdf')])
            if path:export_quote(path,q,self.store.company());messagebox.showinfo('PDF gerado','Orçamento salvo em:\n'+path)
        buttons=ttk.Frame(self.body);buttons.pack(fill='x')
        for label,action in [('Editar',lambda:self.new_quote(selected())),('Duplicar',lambda:self.new_quote(selected(),True)),('Exportar PDF',pdf)]: ttk.Button(buttons,text=label,command=self.safe(action)).pack(side='left',padx=(0,8))
        status=tk.StringVar(value='ENVIADO');ttk.Combobox(buttons,textvariable=status,values=STATUSES,state='readonly',width=12).pack(side='left',padx=8)
        def change():self.store.set_status(selected()['id'],status.get());refresh()
        ttk.Button(buttons,text='Alterar situação',command=self.safe(change)).pack(side='left')
        search.trace_add('write',refresh);tree.bind('<Double-1>',lambda e:self.safe(lambda:self.new_quote(selected()))());refresh()
    def page_company(self):
        heading(self.body,'Minha empresa','Esses dados aparecem no cabeçalho dos seus orçamentos em PDF.')
        values=self.store.company();fields={}
        for key,label in [('name','Nome / razão social *'),('document','CPF / CNPJ'),('phone','Telefone'),('email','E-mail'),('address','Endereço'),('terms','Condições de pagamento padrão')]:
            ttk.Label(self.body,text=label).pack(anchor='w',pady=(7,2));v=tk.StringVar(value=values.get(key,''));fields[key]=v;ttk.Entry(self.body,textvariable=v).pack(fill='x')
        def save():self.store.save_company({k:v.get() for k,v in fields.items()});messagebox.showinfo('Empresa','Dados da empresa salvos.')
        ttk.Button(self.body,text='Salvar dados',style='Primary.TButton',command=self.safe(save)).pack(anchor='e',pady=20)
    def page_backup(self):
        heading(self.body,'Proteja seus dados.','Faça cópias periódicas e guarde-as em um local seguro.')
        ttk.Label(self.body,text='O backup contém clientes, catálogo, empresa e orçamentos. Guarde uma cópia em outro dispositivo.',wraplength=720).pack(anchor='w',pady=20)
        def backup():
            p=filedialog.asksaveasfilename(defaultextension='.db',initialfile='OrcaPrime-Backup-'+datetime.now().strftime('%Y%m%d-%H%M')+'.db',filetypes=[('Backup OrçaPrime','*.db')])
            if p:self.store.backup(p);messagebox.showinfo('Backup','Cópia de segurança criada.')
        def restore():
            p=filedialog.askopenfilename(filetypes=[('Backup OrçaPrime','*.db')])
            if p and messagebox.askyesno('Restaurar backup','Substituir os dados atuais pelo backup? Uma cópia prévia será preservada automaticamente.'):
                self.store.restore(p);messagebox.showinfo('Restauração','Backup restaurado. Abra o programa novamente para entrar com os usuários do backup.');self.closed=True;self.root.destroy()
        ttk.Button(self.body,text='Criar backup',style='Primary.TButton',command=self.safe(backup)).pack(anchor='w',pady=10)
        ttk.Button(self.body,text='Restaurar backup',command=self.safe(restore)).pack(anchor='w',pady=10)
        ttk.Label(self.body,text='Pasta de dados: '+str(self.store.path.parent),style='Sub.TLabel',wraplength=760).pack(anchor='w',pady=30)
    def page_license(self):
        if self.license is None:
            heading(self.body,'OrçaPrime gratuito','Orçamentos, clientes e produtos sem mensalidade.')
            ttk.Label(self.body,text='Funciona sem internet e sem código de ativação.\nSeus dados ficam neste computador. Faça backups regularmente.',wraplength=700).pack(anchor='w',pady=25)
            ttk.Label(self.body,text='Desenvolvido por OLIVERTECH SOLUÇÕES',style='Sub.TLabel').pack(anchor='w')
            return
        heading(self.body,'Minha licença','Sua chave permanece protegida após a ativação.')
        p=self.license.payload
        for label,value in [('Código',p['mask']),('Plano',p['plan']),('Situação','ATIVA'),('Vencimento',datetime.fromtimestamp(p['expires_at']).strftime('%d/%m/%Y %H:%M') if p['expires_at'] else 'Permanente')]:
            ttk.Label(self.body,text=label,style='Sub.TLabel').pack(anchor='w',pady=(12,3));ttk.Label(self.body,text=value,font=(FONT,15,'bold')).pack(anchor='w')
        ttk.Label(self.body,text='A validação é feita ao abrir e durante o uso. Mantenha a conexão com a internet.',wraplength=700).pack(anchor='w',pady=25)
        ttk.Button(self.body,text='Trocar código de ativação',command=lambda:self.show_activation('Informe o novo código.')).pack(anchor='w')
        ttk.Label(self.body,text='OrçaPrime 1.0.0\nDesenvolvido por OLIVERTECH SOLUÇÕES\n© 2026 Mateus Oliveira',style='Sub.TLabel').pack(anchor='w',pady=30)
