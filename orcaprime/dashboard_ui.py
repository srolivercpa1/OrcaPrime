from .widgets import FONT
"""Operational home screen for the local workshop."""
import tkinter as tk
from tkinter import ttk
from datetime import date
from .widgets import heading, NAVY, TEAL, MUTED
from .workshop_ui import scroll_frame
from .workshop_queries import OrderFilters
from .domain import brl


class DashboardPages:
    def open_orders(self, filters=None):
        self.order_filters = filters or OrderFilters()
        self.navigate('orders')

    def page_dashboard(self):
        data = self.workshop.dashboard()
        self.dashboard_values = data
        heading(self.body, 'Central da assistência', 'Atendimentos, prazos e prioridades em um só lugar.')
        body = scroll_frame(self.body)
        top = ttk.Frame(body); top.pack(fill='x', pady=(0,16))
        ttk.Label(top, text=date.today().strftime('%d/%m/%Y'), style='Sub.TLabel').pack(side='left')
        ttk.Button(top, text='+ Nova ordem de serviço', style='Primary.TButton',
                   command=self.safe(self.edit_order)).pack(side='right')
        cards = ttk.Frame(body); cards.pack(fill='x')
        cards.columnconfigure((0,1), weight=1, uniform='cards')
        self.dashboard_cards = {}
        definitions = [
            ('active','EM ANDAMENTO',OrderFilters(active_only=True),NAVY),
            ('overdue','PRAZO VENCIDO',OrderFilters(deadline='overdue'),'#b45309'),
            ('awaiting_approval','AGUARDANDO APROVAÇÃO',OrderFilters(status='AGUARDANDO_APROVACAO'),NAVY),
            ('ready','PRONTAS PARA RETIRADA',OrderFilters(status='PRONTA'),TEAL),
        ]
        for i,(key,label,filters,color) in enumerate(definitions):
            command = self.safe(lambda f=filters:self.open_orders(f))
            button=tk.Button(cards,text=f'{data[key]}\n{label}',command=command,
                font=(FONT,12,'bold'),bg='white',fg=color,activebackground='#e8f5f3',
                activeforeground=color,relief='flat',bd=0,padx=12,pady=20,anchor='w',wraplength=210,
                cursor='hand2',highlightthickness=1,highlightbackground='#dce5ef')
            button.grid(row=i//2,column=i%2,sticky='nsew',padx=5,pady=5)
            self.dashboard_cards[key]=button
        if data['invalid_dates']:
            ttk.Label(body,text=f"{data['invalid_dates']} OS com previsão inválida. Revise as datas.",foreground='#b45309').pack(anchor='w',pady=8)
        shortcuts=ttk.Frame(body);shortcuts.pack(fill='x',pady=16)
        for label,filters in [('Aguardando peça',OrderFilters(status='AGUARDANDO_PECA')),
                              ('Retornos',OrderFilters(returns_only=True)),('Prazos de hoje',OrderFilters(deadline='today'))]:
            ttk.Button(shortcuts,text=label,command=self.safe(lambda f=filters:self.open_orders(f))).pack(side='left',padx=3)
        ttk.Label(body,text='Agenda de atendimentos',font=(FONT,15,'bold')).pack(anchor='w',pady=(8,12))
        for order in data['agenda'][:8]:
            row=ttk.Frame(body,style='Card.TFrame',padding=10);row.pack(fill='x',pady=3)
            label=f"{order['number']}  |  {order.get('customer',{}).get('name','')}\n{order.get('equipment','')}  |  Previsão: {'/'.join(order['due_date'].split('-')[::-1])}"
            ttk.Label(row,text=label,background='white',wraplength=360).pack(side='left',fill='x',expand=True)
            ttk.Button(row,text='Abrir OS',command=self.safe(lambda oid=order['id']:self.edit_order(oid))).pack(side='right')
        if not data['agenda']:
            ttk.Label(body,text='Nenhum prazo agendado. Cadastre um cliente e abra uma OS para começar.',wraplength=480,style='Sub.TLabel').pack(anchor='w')
        if 'finance' in data:
            ttk.Separator(body).pack(fill='x',pady=18)
            ttk.Label(body,text='Financeiro | acumulado das OS',font=(FONT,14,'bold')).pack(anchor='w')
            ttk.Label(body,text=f"Recebido: {brl(data['finance']['received_cents'])}    |    Saldo pendente: {brl(data['finance']['balance_cents'])}",wraplength=480).pack(anchor='w',pady=10)
            ttk.Button(body,text=f"Estoque: {len(data['low_stock'])} peças no mínimo ou abaixo",command=self.safe(lambda:self.navigate('stock'))).pack(anchor='w')
        ttk.Label(body,text='Dados locais | Atualize o painel para consultar novas alterações.',style='Sub.TLabel',wraplength=450).pack(anchor='w',pady=(22,8))
        ttk.Button(body,text='Atualizar painel',command=self.safe(lambda:self.navigate('dashboard'))).pack(anchor='w')
