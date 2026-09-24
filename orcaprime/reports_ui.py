"""Financial summary and delivery productivity, with separate date semantics."""
import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import date
from .widgets import heading, table
from .domain import brl
from .workshop_queries import parsed_date


def render_reports(app):
    app.workshop._allow('FINANCEIRO')
    heading(app.body,'Relatórios da assistência','Entregas por período e situação financeira acumulada.')
    tabs=ttk.Notebook(app.body);tabs.pack(fill='both',expand=True)
    productivity=ttk.Frame(tabs,padding=12);overview=ttk.Frame(tabs,padding=12)
    tabs.add(productivity,text='Produtividade');tabs.add(overview,text='Financeiro e estoque')
    period={k:tk.StringVar(value=v) for k,v in {'start':date.today().replace(day=1).isoformat(),'end':date.today().isoformat()}.items()}
    app.report_period=period
    bar=ttk.Frame(productivity);bar.pack(fill='x')
    for key,label in [('start','De (AAAA-MM-DD)'),('end','Até (AAAA-MM-DD)')]:
        cell=ttk.Frame(bar);cell.pack(side='left',padx=(0,8))
        ttk.Label(cell,text=label).pack(anchor='w');ttk.Entry(cell,textvariable=period[key],width=15).pack()
    export_bar=ttk.Frame(productivity);export_bar.pack(side='bottom',fill='x',pady=8)
    note=ttk.Label(productivity,wraplength=550,style='Sub.TLabel');note.pack(side='bottom',fill='x')
    tree=table(productivity,[('t','Técnico registrado na OS',300),('n','Atendimentos entregues',200)])
    app.productivity_tree=tree
    rows=[]
    def refresh():
        nonlocal rows
        app.guard()
        start=date.fromisoformat(period['start'].get());end=date.fromisoformat(period['end'].get())
        rows=app.workshop.productivity(start,end)
        tree.delete(*tree.get_children())
        for r in rows:tree.insert('','end',values=(r['technician'],r['delivered_count']))
        missing=sum(o['status']=='ENTREGUE' and not any(e.get('action')=='SITUACAO' and e.get('target')=='ENTREGUE' and parsed_date(str(e.get('created_at') or '').split('T')[0].split(' ')[0]) for e in o.get('events',[])) for o in app.workshop.list_orders())
        note.configure(text=f'Critério: primeira entrega registrada no histórico, período inclusivo. Técnico registrado na OS. {missing} OS entregues sem data de evento válida, não incluídas. Recebimentos têm datas próprias e não são receita deste período.')
    app.refresh_productivity=refresh
    ttk.Button(bar,text='Aplicar período',command=app.safe(refresh)).pack(side='left',padx=5,pady=(18,0))
    def export_productivity():
        refresh()
        path=filedialog.asksaveasfilename(parent=app.root,defaultextension='.csv',initialfile='produtividade.csv',filetypes=[('CSV','*.csv')])
        if path:
            with open(path,'w',encoding='utf-8-sig',newline='') as stream:
                writer=csv.writer(stream,delimiter=';');writer.writerow(('Técnico','Entregues','Início','Fim'))
                writer.writerows((r['technician'],r['delivered_count'],period['start'].get(),period['end'].get()) for r in rows)
            messagebox.showinfo('Relatório','Relatório exportado.',parent=app.root)
    ttk.Button(export_bar,text='Exportar produtividade CSV',command=app.safe(export_productivity)).pack(anchor='w',pady=10)
    report=app.workshop.report();overview_rows=[]
    for label,key in [('Recebido nas OS (acumulado)','received_cents'),('Saldo das OS','balance_cents'),('Estoque a custo','stock_value_cents')]:overview_rows.append((label,brl(report[key])))
    for status,count in report['orders_by_status'].items():overview_rows.append(('OS — '+status,str(count)))
    overview_rows += [('Peças no mínimo ou abaixo',str(len(report['low_stock']))),('OS com prazo vencido',str(len(report['overdue'])))]
    for p in report['low_stock']:overview_rows.append(('Estoque — '+p['description'],str(p['quantity'])))
    for result in report['order_results']:overview_rows.append(('Margem orçada — '+result['number']+' / '+result.get('technician',''),brl(result['margin_cents'])))
    overview_export=ttk.Frame(overview);overview_export.pack(side='bottom',fill='x')
    totals=table(overview,[('k','Indicador acumulado',420),('v','Resultado',150)])
    for row in overview_rows:totals.insert('','end',values=row)
    def export_overview():
        app.workshop._allow('FINANCEIRO')
        path=filedialog.asksaveasfilename(parent=app.root,defaultextension='.csv',initialfile='relatorio-oficina.csv',filetypes=[('CSV','*.csv')])
        if path:
            with open(path,'w',encoding='utf-8-sig',newline='') as stream:
                writer=csv.writer(stream,delimiter=';');writer.writerow(('Indicador','Resultado'));writer.writerows(overview_rows)
    ttk.Button(overview_export,text='Exportar resumo CSV',command=app.safe(export_overview)).pack(anchor='w')
    refresh()
