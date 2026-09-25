"""Premium operational dashboard, backed entirely by persisted workshop data."""
import tkinter as tk
from tkinter import ttk
from datetime import date
from .widgets import FONT, heading, table, BG, CARD, TEXT, TEAL, MUTED, BORDER, CYAN
from .modern_widgets import MetricCard, WelcomeBanner
from .branding import brand_header
from .workshop_ui import scroll_frame
from .workshop_queries import OrderFilters
from .domain import brl


class DashboardPages:
    def open_orders(self,filters=None):
        self.order_filters=filters or OrderFilters();self.navigate('orders')

    def dashboard_new_record(self,catalog=False):
        self.navigate('catalog' if catalog else 'customers')
        self.edit_record(True,default_kind='PRODUTO' if catalog else 'SERVIÇO')

    def page_dashboard(self):
        data=self.workshop.dashboard();self.dashboard_values=data
        heading(self.body,'Visão geral','Gestão completa para sua assistência técnica.')
        body=scroll_frame(self.body)
        body.columnconfigure(0,weight=1)
        left=ttk.Frame(body);left.grid(row=0,column=0,sticky='nsew')
        right=ttk.Frame(body);right.grid(row=0,column=1,sticky='new',padx=(18,0))
        WelcomeBanner(left).pack(fill='x',pady=(0,14))
        cards=ttk.Frame(left);cards.pack(fill='x')
        self.dashboard_cards={}
        definitions=[
            ('active','EM ANDAMENTO',OrderFilters(active_only=True),'#159cff','Atendimentos ativos','orders'),
            ('overdue','PRAZO VENCIDO',OrderFilters(deadline='overdue'),'#ff9e16','Prazos para revisar','reports'),
            ('awaiting_approval','AGUARDANDO APROVAÇÃO',OrderFilters(status='AGUARDANDO_APROVACAO'),'#10cba0','Aguardando cliente','warranties'),
            ('ready','PRONTAS PARA RETIRADA',OrderFilters(status='PRONTA'),'#ae82ff','Serviços concluídos','quotes')]
        for key,label,filters,color,detail,icon in definitions:
            self.dashboard_cards[key]=MetricCard(cards,data[key],label,color,self.safe(lambda f=filters:self.open_orders(f)),detail,icon)
        def layout_cards(event=None):
            columns=4 if cards.winfo_width()>=820 else 2
            for i in range(4):cards.columnconfigure(i,weight=1 if i<columns else 0,uniform='metrics' if i<columns else '')
            for i,card in enumerate(self.dashboard_cards.values()):card.grid(row=i//columns,column=i%columns,sticky='nsew',padx=(0,8 if i%columns<columns-1 else 0),pady=(0,10))
        cards.bind('<Configure>',layout_cards);layout_cards()
        def panel(parent,title):
            outer=tk.Frame(parent,bg=CARD,highlightbackground=BORDER,highlightthickness=1,padx=16,pady=16)
            outer.pack(fill='x',pady=(0,16))
            tk.Label(outer,text=title,bg=CARD,fg=TEXT,font=(FONT,13,'bold'),anchor='w').pack(fill='x',pady=(0,14))
            return outer
        quick=panel(right,'Ações rápidas')
        for label,style,action in [('+  Nova OS','Primary',self.edit_order),('Novo cliente','Success',lambda:self.dashboard_new_record(False)),('Novo orçamento','Purple',self.new_quote),('Adicionar produto','',lambda:self.dashboard_new_record(True))]:
            ttk.Button(quick,text=label,style=(style+'.TButton') if style else 'TButton',command=self.safe(action)).pack(fill='x',pady=4)
        today=panel(right,'Hoje  |  '+date.today().strftime('%d/%m/%Y'))
        count=len(self.workshop.query_orders(OrderFilters(deadline='today',active_only=True)))
        tk.Label(today,text=str(count),font=(FONT,32,'bold'),bg=CARD,fg=CYAN).pack()
        tk.Label(today,text='OS com prazo para hoje' if count else 'Nenhuma OS prevista para hoje',font=(FONT,10),bg=CARD,fg=MUTED,wraplength=245).pack(pady=8)
        ttk.Button(today,text='Ver prazos de hoje',command=self.safe(lambda:self.open_orders(OrderFilters(deadline='today',active_only=True)))).pack(fill='x',pady=8)
        brand=panel(right,'Mais organização.')
        brand_header(brand,CARD,48).pack(anchor='w')
        tk.Label(brand,text='Mais resultados.',font=(FONT,14,'bold'),bg=CARD,fg=CYAN).pack(pady=(14,0))
        if data['invalid_dates']:
            ttk.Label(left,text=f"{data['invalid_dates']} OS com previsão inválida. Revise as datas.",foreground='#ffaf55').pack(anchor='w',pady=8)
        shortcuts=ttk.Frame(left);shortcuts.pack(fill='x',pady=(4,16))
        for label,filters in [('Aguardando peça',OrderFilters(status='AGUARDANDO_PECA')),('Retornos',OrderFilters(returns_only=True)),('Prazos de hoje',OrderFilters(deadline='today'))]:
            ttk.Button(shortcuts,text=label,command=self.safe(lambda f=filters:self.open_orders(f))).pack(side='left',padx=(0,6))
        agenda=panel(left,'Agenda de atendimentos')
        ttk.Button(agenda,text='+ Nova ordem de serviço',style='Primary.TButton',command=self.safe(self.edit_order)).pack(anchor='e',pady=(0,10))
        tree=table(agenda,[('os','OS',130),('client','Cliente',155),('device','Equipamento',160),('due','Previsão',100),('status','Situação',190)])
        tree.configure(height=5)
        for order in data['agenda'][:30]:
            tree.insert('','end',iid=str(order['id']),values=(order['number'],order.get('customer',{}).get('name',''),order.get('equipment',''),'/'.join(order['due_date'].split('-')[::-1]),order['status'].replace('_',' ')))
        def open_selected(event=None):
            if tree.selection():self.safe(lambda:self.edit_order(int(tree.selection()[0])))()
        tree.bind('<Double-1>',open_selected)
        ttk.Button(agenda,text='Abrir OS selecionada',command=open_selected).pack(anchor='e')
        if not data['agenda']:
            tk.Label(agenda,text='Nenhum prazo agendado. Abra uma OS para começar.',bg=CARD,fg=MUTED,wraplength=440).pack(pady=12)
        if 'finance' in data:
            finance=panel(left,'Financeiro | acumulado das OS')
            tk.Label(finance,text=f"Recebido: {brl(data['finance']['received_cents'])}    |    Pendente: {brl(data['finance']['balance_cents'])}",bg=CARD,fg=MUTED,wraplength=500).pack(anchor='w')
            ttk.Button(finance,text=f"Estoque: {len(data['low_stock'])} peças no mínimo ou abaixo",command=self.safe(lambda:self.navigate('stock'))).pack(anchor='w',pady=(12,0))
        ttk.Button(left,text='Atualizar painel',command=self.safe(lambda:self.navigate('dashboard'))).pack(anchor='w',pady=8)
        def responsive(event=None):
            wide=body.winfo_width()>=1020
            right.grid(row=0 if wide else 1,column=1 if wide else 0,sticky='new',padx=(18,0) if wide else 0,pady=(0,0) if wide else (18,0))
            body.columnconfigure(1,weight=0,minsize=286 if wide else 0)
        body.bind('<Configure>',responsive,add='+');responsive()
