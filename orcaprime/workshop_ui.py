from .widgets import FONT
"""Desktop pages for the offline service workshop."""
import csv
import json
import uuid
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from .widgets import heading, table
from .domain import brl, decimal_text


def scroll_frame(parent):
    outer=ttk.Frame(parent);outer.pack(fill='both',expand=True)
    canvas=tk.Canvas(outer,highlightthickness=0);bar=ttk.Scrollbar(outer,command=canvas.yview)
    canvas.configure(yscrollcommand=bar.set);bar.pack(side='right',fill='y');canvas.pack(fill='both',expand=True)
    inner=ttk.Frame(canvas,padding=15);window=canvas.create_window((0,0),window=inner,anchor='nw')
    inner.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.bind('<Configure>',lambda e:canvas.itemconfigure(window,width=e.width))
    return inner


class WorkshopPages:
    def _dialog(self,title,fields,values,save):
        win=tk.Toplevel(self.root);win.title(title);win.geometry('570x590');win.transient(self.root)
        bottom=ttk.Frame(win,padding=12);bottom.pack(side='bottom',fill='x')
        body=scroll_frame(win);variables={}
        for key,label,options in fields:
            ttk.Label(body,text=label).pack(anchor='w',pady=(8,3))
            var=tk.StringVar(value=values.get(key,''));variables[key]=var
            widget=ttk.Combobox(body,textvariable=var,values=options,state='readonly') if options else ttk.Entry(body,textvariable=var)
            widget.pack(fill='x')
        initial={k:v.get() for k,v in variables.items()}
        def close():
            if initial!={k:v.get() for k,v in variables.items()} and not messagebox.askyesno('Descartar alterações?','Fechar sem salvar as alterações?',parent=win):return
            win.destroy()
        def submit():
            self.guard();save({k:v.get() for k,v in variables.items()});win.destroy()
        ttk.Button(bottom,text='Cancelar',command=close).pack(side='left')
        ttk.Button(bottom,text='Salvar',style='Primary.TButton',command=self.safe(submit)).pack(side='right')
        win.protocol('WM_DELETE_WINDOW',close)
        return win

    def _selected(self,tree):
        selected=tree.selection()
        if not selected:raise ValueError('Selecione um registro.')
        return int(selected[0])

    def page_orders(self):
        self._orders_page(False)

    def page_warranties(self):
        self._orders_page(True)

    def _orders_page(self,warranty):
        from .workshop import STATUSES
        from .workshop_queries import OrderFilters, PRIORITIES, priority
        initial=getattr(self,'order_filters',OrderFilters()) if not warranty else OrderFilters(returns_only=False)
        self.order_filters=initial
        heading(self.body,'Garantias e retornos' if warranty else 'Ordens de serviço','Acompanhe a oficina por técnico, prioridade, situação e prazo.')
        controls=ttk.Frame(self.body);controls.pack(fill='x')
        search=tk.StringVar(value=initial.text);status=tk.StringVar(value=initial.status or 'TODAS')
        technician=tk.StringVar(value=initial.technician);urgency=tk.StringVar(value=initial.priority or 'TODAS')
        deadlines={'Todos os prazos':'','Atrasadas':'overdue','Hoje':'today','Sem previsão':'undated'}
        deadline=tk.StringVar(value=next(k for k,v in deadlines.items() if v==initial.deadline))
        active=tk.BooleanVar(value=initial.active_only)
        returns=tk.BooleanVar(value=initial.returns_only);view=tk.StringVar(value='Tabela')
        all_orders=self.workshop.list_orders()
        techs=sorted({o.get('technician','').strip() for o in all_orders if o.get('technician','').strip()})
        for col,(label,var,values) in enumerate([
            ('Pesquisar',search,None),('Situação',status,('TODAS',)+tuple(STATUSES)),
            ('Técnico',technician,['']+techs),('Prioridade',urgency,('TODAS',)+PRIORITIES),
            ('Previsão',deadline,tuple(deadlines)),('Visualização',view,('Tabela','Etapas'))]):
            cell=ttk.Frame(controls);cell.grid(row=col//3,column=col%3,sticky='ew',padx=(0,8),pady=4)
            ttk.Label(cell,text=label,style='Sub.TLabel').pack(anchor='w')
            widget=ttk.Combobox(cell,textvariable=var,values=values,state='readonly',width=17) if values is not None else ttk.Entry(cell,textvariable=var,width=17)
            widget.pack(fill='x');controls.columnconfigure(col%3,weight=1)
        actions=ttk.Frame(self.body);actions.pack(fill='x',pady=8)
        ttk.Button(actions,text='+ Nova OS',style='Primary.TButton',command=self.safe(lambda:self.edit_order())).pack(side='right')
        count=ttk.Label(actions,style='Sub.TLabel');count.pack(side='left')
        ttk.Checkbutton(actions,text='Retornos',variable=returns).pack(side='left',padx=4)
        ttk.Checkbutton(actions,text='Em andamento',variable=active).pack(side='left',padx=4)
        footer=ttk.Frame(self.body);footer.pack(side='bottom',fill='x',pady=8)
        host=ttk.Frame(self.body);host.pack(fill='both',expand=True)
        self.orders_tree=None
        def selected():
            if self.orders_tree is None:raise ValueError('Selecione uma OS na visualização em tabela.')
            return self._selected(self.orders_tree)
        def refresh(*_):
            filters=OrderFilters(search.get(),'' if status.get()=='TODAS' else status.get(),technician.get(),
                '' if urgency.get()=='TODAS' else urgency.get(),deadlines[deadline.get()],returns.get(),active.get())
            self.order_filters=filters
            orders=self.workshop.query_orders(filters)
            if warranty:orders=[o for o in orders if o.get('warranty_days') or o.get('parent_id')]
            count.configure(text=f'{len(orders)} atendimento(s)')
            for child in host.winfo_children():child.destroy()
            self.orders_tree=None
            if view.get()=='Tabela':
                tree=table(host,[('n','OS',125),('c','Cliente',170),('e','Equipamento',150),('t','Técnico',115),('p','Prioridade',100),('d','Previsão',110),('s','Situação',165)])
                self.orders_tree=tree
                tree.tag_configure('urgent',foreground='#ffad56')
                for o in orders:
                    tree.insert('','end',iid=str(o['id']),values=(o['number'],o.get('customer',{}).get('name',''),o.get('equipment',''),o.get('technician') or 'Sem técnico',priority(o),'/'.join(o.get('due_date','').split('-')[::-1]),o['status']),tags=('urgent',) if priority(o)=='URGENTE' else ())
                tree.bind('<Double-1>',lambda e:self.safe(lambda:self.edit_order(selected()))())
            else:
                board=scroll_frame(host)
                for state in STATUSES:
                    group=[o for o in orders if o['status']==state]
                    if not group:continue
                    ttk.Label(board,text=state.replace('_',' ').capitalize()+f' | {len(group)}',font=(FONT,12,'bold')).pack(anchor='w',pady=(12,5))
                    for o in group:
                        ttk.Button(board,text=f"{o['number']} | {o.get('customer',{}).get('name','')} | {priority(o)}",command=self.safe(lambda oid=o['id']:self.edit_order(oid))).pack(fill='x',pady=3)
                if not orders:ttk.Label(board,text='Nenhuma OS encontrada para estes filtros.').pack(pady=20)
        def clear():
            search.set('');status.set('TODAS');technician.set('');urgency.set('TODAS');deadline.set('Todos os prazos');returns.set(False);active.set(False)
        ttk.Button(footer,text='Abrir OS selecionada',command=self.safe(lambda:self.edit_order(selected()))).pack(side='left')
        ttk.Button(footer,text='Imprimir documentos',command=self.safe(lambda:self.document_dialog(selected()))).pack(side='left',padx=8)
        ttk.Button(footer,text='Limpar filtros',command=self.safe(clear)).pack(side='right')
        for var in (search,status,technician,urgency,deadline,returns,active,view):var.trace_add('write',lambda *_:self.safe(refresh)())
        refresh()

    def edit_order(self,order_id=None):
        from .workshop import STATUSES
        customers=self.store.list_customers()
        if not customers:raise ValueError('Cadastre um cliente antes de abrir a ordem de serviço.')
        order=self.workshop.get_order(order_id) if order_id else {}
        win=tk.Toplevel(self.root);win.title('Ordem de serviço '+str(order.get('number','Nova')));win.geometry('990x740');win.minsize(750,560);win.transient(self.root)
        bottom=ttk.Frame(win,padding=12);bottom.pack(side='bottom',fill='x')
        summary=ttk.Label(win,padding=12);summary.pack(fill='x')
        notebook=ttk.Notebook(win);notebook.pack(fill='both',expand=True,padx=12)
        tabs={}
        for name in ('Entrada','Diagnóstico e entrega','Itens','Pagamentos','Histórico e anexos','Documentos'):
            tab=ttk.Frame(notebook);notebook.add(tab,text=name);tabs[name]=tab
        variables={};customers_map={str(c['id'])+' — '+c['name']:c['id'] for c in customers}
        fields=[('customer_id','Cliente *',tuple(customers_map)),('equipment','Equipamento *',None),('brand','Marca',None),('model','Modelo',None),('serial','Número de série / IMEI',None),('accessories','Acessórios recebidos',None),('complaint','Defeito relatado *',None),('checklist','Estado de conservação / checklist de entrada',None)]
        diagnostic=[('diagnosis','Diagnóstico técnico',None),('technician','Técnico responsável',None),('priority','Prioridade',('BAIXA','NORMAL','ALTA','URGENTE')),('due_date','Previsão (AAAA-MM-DD)',None),('warranty_days','Garantia (dias)',None),('warranty_terms','Condições da garantia',None),('receiver','Recebedor na entrega',None),('final_checklist','Checklist final / testes',None),('notes','Serviços executados / observações públicas (impressas)',None),('internal_notes','Observações internas (não impressas)',None)]
        from .widgets import TextValue
        from .order_templates import append_checklist
        for tab,group in [('Entrada',fields),('Diagnóstico e entrega',diagnostic)]:
            body=scroll_frame(tabs[tab])
            for key,label,options in group:
                ttk.Label(body,text=label).pack(anchor='w',pady=(8,3));value=order.get(key,'0' if key=='warranty_days' else '')
                if key=='priority':value=value or 'NORMAL'
                if key=='customer_id':value=next((k for k,v in customers_map.items() if v==order.get('customer_id')),next(iter(customers_map)))
                if key in ('complaint','checklist','diagnosis','notes','final_checklist','warranty_terms','internal_notes'):
                    widget=tk.Text(body,height=4,wrap='word',font=(FONT,10),relief='solid',bd=1)
                    var=TextValue(widget);var.set(value);widget.pack(fill='x')
                else:
                    var=tk.StringVar(value=value)
                    (ttk.Combobox(body,textvariable=var,values=options,state='readonly') if options else ttk.Entry(body,textvariable=var)).pack(fill='x')
                variables[key]=var
                if key=='checklist':
                    category=tk.StringVar(value='celular');row=ttk.Frame(body);row.pack(fill='x',pady=5)
                    ttk.Combobox(row,textvariable=category,values=('celular','computador','outros'),state='readonly',width=14).pack(side='left')
                    ttk.Button(row,text='Inserir checklist',command=self.safe(lambda:variables['checklist'].set(append_checklist(variables['checklist'].get(),category.get())))).pack(side='left',padx=8)
        win.order_fields=variables
        initial={k:v.get() for k,v in variables.items()}
        itemtree=table(tabs['Itens'],[('d','Descrição',260),('q','Quantidade',100),('p','Preço',100),('t','Total',100)])
        paytree=table(tabs['Pagamentos'],[('d','Data',160),('m','Forma',120),('a','Valor',110),('s','Situação',130)])
        history= tk.Text(tabs['Histórico e anexos'],height=8,wrap='word');history.pack(fill='both',expand=True,padx=8,pady=8)
        attachments=ttk.Combobox(tabs['Histórico e anexos'],state='readonly');attachments.pack(fill='x',padx=8)
        def refresh():
            nonlocal order
            if order_id:order=self.workshop.get_order(order_id)
            summary.configure(text=f"{order.get('number','Nova OS')} | {order.get('status','Entrada')} | Total: {brl(order.get('total_cents',0))} | Pago: {brl(order.get('paid_cents',0))} | Saldo: {brl(order.get('balance_cents',0))} | Garantia: {order.get('warranty_days',0)} dias")
            itemtree.delete(*itemtree.get_children());paytree.delete(*paytree.get_children())
            for i in order.get('items',[]):itemtree.insert('','end',iid=str(i['id']),values=(i['description'],i['quantity'],brl(i.get('price_cents',0)),brl(i.get('total_cents',0))))
            for p in order.get('payments',[]):paytree.insert('','end',iid=str(p['id']),values=(p.get('created_at',''),p.get('method',''),brl(p['amount_cents']),'Estornado' if p.get('reversed') else 'Recebido'))
            history.configure(state='normal');history.delete('1.0','end')
            history.insert('end','\n\n'.join(f"{e.get('created_at','')} | {e.get('kind',e.get('action',''))}\n{e.get('note','')}" for e in order.get('events',[])));history.configure(state='disabled')
            attachments.configure(values=[f"{a['id']} — {a.get('filename',a.get('name','Anexo'))}" for a in order.get('attachments',[])])
        def save():
            nonlocal order_id,initial
            data={k:v.get() for k,v in variables.items()};data['customer_id']=customers_map[data['customer_id']]
            
            if order_id and getattr(self,'actor',{}).get('role')=='FINANCEIRO':data={k:data[k] for k in ('receiver','final_checklist')}
            result=self.workshop.save_order(data,order_id);order_id=result['id'] if isinstance(result,dict) else result
            initial={k:v.get() for k,v in variables.items()};refresh()
        def require_saved():
            if not order_id:raise ValueError('Salve a entrada da OS antes de continuar.')
        def additem():
            require_saved();request_id=str(uuid.uuid4());parts=self.workshop.list_parts();mapping={'Serviço / item avulso':None};mapping.update({f"{p['id']} — {p['description']}":p['id'] for p in parts})
            def submit(d):
                part=mapping[d.pop('part')]
                if part:
                    selected=next(p for p in parts if p['id']==part)
                    d['part_id']=part;d['kind']='PECA';d['cost']=decimal_text(selected['cost_cents'])
                    if not d['description'].strip():d['description']=selected['description']
                    if not d['price'].strip():d['price']=decimal_text(selected['price_cents'])
                self.workshop.add_item(order_id,dict(d,request_id=request_id));refresh()
            self._dialog('Adicionar item',[('part','Peça do estoque',tuple(mapping)),('description','Descrição *',None),('quantity','Quantidade *',None),('price','Preço unitário (R$) — vazio usa preço da peça',None),('cost','Custo unitário do serviço (R$)',None)],{'part':next(iter(mapping)),'quantity':'1','price':'','cost':'0,00'},submit)
        def removeitem():
            require_saved();self.workshop.remove_item(order_id,self._selected(itemtree));refresh()
        bar=ttk.Frame(tabs['Itens']);bar.pack(fill='x',padx=8,pady=8)
        for label,action in [('Adicionar peça / serviço',additem),('Remover item',removeitem)]:ttk.Button(bar,text=label,command=self.safe(action)).pack(side='left',padx=4)
        def payment():
            require_saved();request_id=str(uuid.uuid4())
            def submit(d):self.workshop.record_payment(order_id,dict(d,request_id=request_id));refresh()
            self._dialog('Receber pagamento',[('amount','Valor (R$)',None),('method','Forma',('PIX','DINHEIRO','CARTÃO','TRANSFERÊNCIA','OUTRO'))],{'amount':decimal_text(order.get('balance_cents',0)),'method':'PIX'},submit)
        def reverse():
            require_saved();pid=self._selected(paytree)
            def submit(d):self.workshop.reverse_payment(pid,d['note']);refresh()
            self._dialog('Estornar pagamento',[('note','Motivo obrigatório',None)],{},submit)
        bar=ttk.Frame(tabs['Pagamentos']);bar.pack(fill='x',padx=8,pady=8)
        for label,action in [('Receber pagamento',payment),('Estornar selecionado',reverse)]:ttk.Button(bar,text=label,command=self.safe(action)).pack(side='left',padx=4)
        def attach():
            require_saved();path=filedialog.askopenfilename(parent=win)
            if path:self.workshop.add_attachment(order_id,path);refresh()
        def openattach():
            from .service_documents import open_document
            require_saved()
            if not attachments.get():raise ValueError('Selecione um anexo.')
            aid=int(attachments.get().split(' — ')[0]);a=next(a for a in order['attachments'] if a['id']==aid)
            path=filedialog.asksaveasfilename(parent=win,initialfile=Path(a.get('filename',a.get('name','anexo'))).name)
            if path:
                _,content=self.workshop.attachment_bytes(aid);Path(path).write_bytes(content)
                if Path(path).suffix.lower()=='.pdf':open_document(path)
                else:messagebox.showinfo('Anexo salvo','Arquivo salvo em: '+path,parent=win)
        bar=ttk.Frame(tabs['Histórico e anexos']);bar.pack(fill='x',padx=8,pady=8)
        ttk.Button(bar,text='Adicionar foto / anexo',command=self.safe(attach)).pack(side='left');ttk.Button(bar,text='Salvar anexo / abrir PDF',command=self.safe(openattach)).pack(side='left',padx=8)
        def open_documents():
            require_saved()
            if initial!={k:v.get() for k,v in variables.items()}:raise ValueError('Salve os dados da OS antes de gerar o documento.')
            snapshot={k:v.get() for k,v in variables.items()}
            def ensure_saved():
                if snapshot!={k:v.get() for k,v in variables.items()}:raise ValueError('A OS foi alterada. Salve e reabra a central de documentos.')
            self.document_dialog(order_id,ensure_saved)
        docbody=scroll_frame(tabs['Documentos'])
        ttk.Label(docbody,text='OS, entrada, entrega, garantia, recibo e etiqueta',font=(FONT,13,'bold'),wraplength=500).pack(anchor='w',pady=15)
        ttk.Button(docbody,text='Abrir central de impressão',style='Primary.TButton',command=self.safe(open_documents)).pack(anchor='w')
        ttk.Label(docbody,text='Os documentos usam os dados salvos. Observações internas não são impressas.',wraplength=500).pack(anchor='w',pady=15)
        def transition():
            require_saved()
            def submit(d):
                if initial!={k:v.get() for k,v in variables.items()}:save()
                self.workshop.transition(order_id,d['status'],d['note']);refresh()
            self._dialog('Alterar situação',[('status','Nova situação',tuple(STATUSES)),('note','Motivo / autorização do cliente',None)],{'status':order['status']},submit)
        def warranty():
            require_saved()
            def submit(d):
                result=self.workshop.create_return(order_id,d['complaint']);self.edit_order(result['id'] if isinstance(result,dict) else result)
            self._dialog('Retorno em garantia',[('complaint','Defeito relatado no retorno',None)],{},submit)
        def equipment_history():
            from .workshop_queries import equipment_history as find_history
            result=find_history(self.workshop.list_orders(),customers_map[variables['customer_id'].get()],variables['serial'].get())
            hist=tk.Toplevel(win);hist.title('Histórico do equipamento' if result['scope']=='equipment' else 'Histórico do cliente — equipamento sem serial');hist.geometry('800x450')
            tree=table(hist,[('n','OS',160),('e','Equipamento',180),('s','Situação',180)])
            for o in result['orders']:tree.insert('','end',iid=str(o['id']),values=(o['number'],o.get('equipment',''),o['status']))
            ttk.Button(hist,text='Abrir atendimento',command=self.safe(lambda:self.edit_order(self._selected(tree)))).pack(pady=8)
        ttk.Button(tabs['Histórico e anexos'],text='Histórico do equipamento / cliente',command=self.safe(equipment_history)).pack(anchor='w',padx=8,pady=8)
        def close():
            if initial!={k:v.get() for k,v in variables.items()} and not messagebox.askyesno('Descartar alterações?','Fechar sem salvar as alterações?',parent=win):return
            win.destroy();self.navigate('orders')
        for label,action in [('Salvar dados',save),('Alterar situação',transition),('Retorno em garantia',warranty),('Fechar',close)]:ttk.Button(bottom,text=label,command=self.safe(action)).pack(side='left',padx=4)
        win.protocol('WM_DELETE_WINDOW',close);refresh()

    def document_dialog(self, order_id, ensure_saved=None):
        from .document_actions import DocumentActions
        from .service_documents import KINDS, PAPERS, list_printers, open_document
        order=self.workshop.get_order(order_id)
        actions=DocumentActions(self.workshop,self.store.company())
        win=tk.Toplevel(self.root);win.title('Central de impressão | '+order['number']);win.geometry('600x550');win.transient(self.root)
        body=ttk.Frame(win,padding=24);body.pack(fill='both',expand=True)
        heading(body,'Documentos da OS',order['number']+' | '+order.get('customer',{}).get('name',''))
        kind=tk.StringVar(value='OS');paper=tk.StringVar(value='A4');printer=tk.StringVar()
        settings=self._printer_settings()
        ttk.Label(body,text='Tipo de documento').pack(anchor='w')
        ttk.Combobox(body,textvariable=kind,values=tuple(KINDS),state='readonly').pack(fill='x',pady=(4,12))
        ttk.Label(body,text='Papel').pack(anchor='w')
        paper_box=ttk.Combobox(body,textvariable=paper,values=('A4','58mm','80mm'),state='readonly');paper_box.pack(fill='x',pady=(4,12))
        ttk.Label(body,text='Impressora instalada').pack(anchor='w')
        notice=tk.StringVar(value='Documentos administrativos | não são notas fiscais.')
        try:names=list_printers()
        except (ValueError,OSError,RuntimeError) as exc:names=[];notice.set(str(exc))
        names=[n.get('name','') if isinstance(n,dict) else n for n in names]
        ttk.Combobox(body,textvariable=printer,values=['']+names,state='readonly').pack(fill='x',pady=(4,12))
        def defaults(*_):printer.set(settings.get(paper.get(),'') if settings.get(paper.get(),'') in names else '')
        def changed_kind(*_):
            paper_box.configure(values=('ETIQUETA',) if kind.get()=='ETIQUETA' else ('A4','58mm','80mm'))
            if kind.get()=='ETIQUETA':paper.set('ETIQUETA')
            elif paper.get()=='ETIQUETA':paper.set('A4')
        paper.trace_add('write',defaults);kind.trace_add('write',changed_kind);defaults()
        ttk.Label(body,textvariable=notice,wraplength=500,style='Sub.TLabel').pack(fill='x',pady=14)
        def generate(mode):
            if ensure_saved:ensure_saved()
            if mode=='print' and not printer.get():raise ValueError('Selecione uma impressora. Você também pode salvar o PDF.')
            path=filedialog.asksaveasfilename(parent=win,defaultextension='.pdf',initialfile=kind.get()+'-'+order['number']+'.pdf',filetypes=[('PDF','*.pdf')])
            result=actions.generate(order_id,path,kind.get(),paper.get())
            if not result:return
            if mode=='preview':open_document(result);notice.set('PDF salvo e enviado ao leitor para pré-visualização.')
            elif mode=='print':actions.send(result,printer.get());notice.set('PDF enviado ao leitor/fila. Confira a impressão no equipamento.')
            else:notice.set('PDF salvo: '+str(result))
        bar=ttk.Frame(body);bar.pack(fill='x',pady=10)
        for label,mode in [('Salvar PDF','save'),('Pré-visualizar','preview'),('Imprimir','print')]:
            ttk.Button(bar,text=label,command=self.safe(lambda m=mode:generate(m))).pack(side='left',padx=3)

    def page_stock(self):
        heading(self.body,'Estoque de peças','Entradas, saídas e ajustes preservam o histórico de movimentações.')
        bar=ttk.Frame(self.body);bar.pack(fill='x');search=tk.StringVar();ttk.Entry(bar,textvariable=search).pack(side='left')
        tree=table(self.body,[('s','Código',110),('d','Descrição',240),('q','Saldo',90),('m','Mínimo',90),('p','Preço',110)])
        def refresh(*_):
            tree.delete(*tree.get_children())
            for p in self.workshop.list_parts():
                if search.get().casefold() not in str(p).casefold():continue
                tree.insert('','end',iid=str(p['id']),values=(p.get('sku',''),p['description'],p.get('quantity','0'),p.get('minimum','0'),brl(p.get('price_cents',0))))
        def edit(new=False):
            p={} if new else next(p for p in self.workshop.list_parts() if p['id']==self._selected(tree))
            def submit(d):self.workshop.save_part(d,p.get('id'));refresh()
            self._dialog('Peça',[('description','Descrição *',None),('sku','Código',None),('price','Preço de venda (R$)',None),('cost','Custo (R$)',None),('minimum','Estoque mínimo',None)],dict(p,price=decimal_text(p.get('price_cents',0)),cost=decimal_text(p.get('cost_cents',0)),minimum=p.get('minimum','0')),submit)
        def move():
            pid=self._selected(tree)
            def submit(d):self.workshop.stock_move(pid,d['quantity'],d['kind'],d['note']);refresh()
            self._dialog('Movimentar estoque',[('kind','Tipo',('ENTRADA','SAIDA','AJUSTE')),('quantity','Quantidade (negativa para saída / redução)',None),('note','Motivo / referência',None)],{'kind':'ENTRADA'},submit)
        def movements():
            pid=self._selected(tree);win=tk.Toplevel(self.root);win.title('Histórico de estoque');win.geometry('800x450')
            listing=table(win,[('d','Data',180),('k','Tipo',120),('q','Quantidade',100),('n','Motivo',300)])
            for m in self.workshop.list_movements():
                if m['part_id']!=pid:continue
                listing.insert('','end',values=(m.get('created_at',''),m.get('kind',''),m.get('quantity',''),m.get('note','')))
        for label,action in [('Nova peça',lambda:edit(True)),('Editar',edit),('Movimentar',move),('Histórico',movements)]:ttk.Button(bar,text=label,command=self.safe(action)).pack(side='right',padx=3)
        search.trace_add('write',refresh);refresh()

    def page_suppliers(self):
        heading(self.body,'Fornecedores','Contatos e dados para compras de peças e insumos.')
        tree=table(self.body,[('n','Nome',240),('d','Documento',180),('p','Telefone',160),('e','E-mail',200)])
        def refresh():
            tree.delete(*tree.get_children())
            for s in self.workshop.list_suppliers():tree.insert('','end',iid=str(s['id']),values=tuple(s.get(k,'') for k in ('name','document','phone','email')))
        def edit(new=False):
            s={} if new else next(s for s in self.workshop.list_suppliers() if s['id']==self._selected(tree))
            def submit(d):self.workshop.save_supplier(d,s.get('id'));refresh()
            self._dialog('Fornecedor',[(k,l,None) for k,l in [('name','Nome *'),('document','CPF / CNPJ'),('phone','Telefone'),('email','E-mail'),('address','Endereço')]],s,submit)
        bar=ttk.Frame(self.body);bar.pack(fill='x');ttk.Button(bar,text='Novo fornecedor',command=self.safe(lambda:edit(True))).pack(side='left');ttk.Button(bar,text='Editar selecionado',command=self.safe(edit)).pack(side='left',padx=8)
        tree.bind('<Double-1>',lambda e:self.safe(edit)());refresh()

    def page_finance(self):
        heading(self.body,'Financeiro','Recebimentos das OS, contas a pagar e receber, e livro-caixa.')
        totals=ttk.Label(self.body);totals.pack(fill='x')
        tabs=ttk.Notebook(self.body);tabs.pack(fill='both',expand=True);accounts=ttk.Frame(tabs);cash=ttk.Frame(tabs);balances=ttk.Frame(tabs)
        tabs.add(accounts,text='Contas');tabs.add(cash,text='Caixa');tabs.add(balances,text='Saldos das OS')
        at=table(accounts,[('d','Descrição',220),('k','Tipo',100),('v','Vencimento',120),('a','Valor',110),('s','Situação',120)])
        ct=table(cash,[('d','Data',160),('n','Descrição',230),('k','Tipo',110),('a','Valor',110)])
        bt=table(balances,[('n','OS',110),('c','Cliente',220),('s','Situação',160),('b','Saldo',130)])
        def refresh():
            for t in (at,ct,bt):t.delete(*t.get_children())
            rows=self.workshop.list_cash();incoming=sum(c['amount_cents'] for c in rows if c['amount_cents']>0);outgoing=sum(-c['amount_cents'] for c in rows if c['amount_cents']<0)
            totals.configure(text=f'Entradas: {brl(incoming)} | Saídas: {brl(outgoing)} | Saldo de caixa: {brl(incoming-outgoing)}')
            for a in self.workshop.list_accounts():at.insert('','end',iid=str(a['id']),values=(a['description'],a['kind'],a.get('due_date',''),brl(a['amount_cents']),'Liquidada' if a.get('settled') else 'Em aberto'))
            for c in rows:ct.insert('','end',iid=str(c['id']),values=(c.get('created_at',''),c.get('description','Pagamento de OS'),c.get('kind','ENTRADA' if c['amount_cents']>0 else 'SAIDA'),brl(c['amount_cents'])))
            for o in self.workshop.list_orders():
                if o['balance_cents']>0:bt.insert('','end',iid=str(o['id']),values=(o['number'],o['customer']['name'],o['status'],brl(o['balance_cents'])))
        def account():
            def submit(d):self.workshop.save_installments(d);refresh()
            self._dialog('Nova conta',[('description','Descrição *',None),('kind','Tipo',('PAGAR','RECEBER')),('amount','Valor (R$)',None),('due_date','Primeiro vencimento (AAAA-MM-DD)',None),('installments','Número de parcelas',None)],{'kind':'PAGAR','installments':'1'},submit)
        def settle():
            aid=self._selected(at)
            def submit(d):self.workshop.settle_account(aid,d['method']);refresh()
            self._dialog('Liquidar conta',[('method','Forma de pagamento',('PIX','DINHEIRO','CARTÃO','TRANSFERÊNCIA','OUTRO'))],{'method':'PIX'},submit)
        def entry():
            def submit(d):self.workshop.cash_entry(d);refresh()
            self._dialog('Lançamento no caixa',[('description','Descrição *',None),('kind','Tipo',('ENTRADA','SAIDA')),('amount','Valor (R$)',None),('method','Forma',('PIX','DINHEIRO','CARTÃO','TRANSFERÊNCIA','OUTRO'))],{'kind':'SAIDA','method':'DINHEIRO'},submit)
        bar=ttk.Frame(accounts);bar.pack(fill='x');ttk.Button(bar,text='Nova conta',command=self.safe(account)).pack(side='left');ttk.Button(bar,text='Liquidar selecionada',command=self.safe(settle)).pack(side='left',padx=8)
        cashbar=ttk.Frame(cash);cashbar.pack(fill='x')
        def open_cash():
            def submit(d):self.workshop.open_cash(d['amount']);refresh()
            self._dialog('Abrir caixa',[('amount','Saldo inicial em dinheiro (R$)',None)],{'amount':'0,00'},submit)
        def close_cash():
            def submit(d):self.workshop.close_cash(d['amount'],d['note']);refresh()
            self._dialog('Fechar caixa',[('amount','Dinheiro contado (R$)',None),('note','Observações / divergência',None)],{},submit)
        def sessions():
            win=tk.Toplevel(self.root);win.title('Histórico de caixas');win.geometry('900x450')
            tree=table(win,[('o','Abertura',150),('c','Fechamento',150),('i','Inicial',100),('e','Esperado',100),('r','Contado',100),('d','Diferença',100)])
            for row in self.workshop.list_cash_sessions():tree.insert('','end',values=(row['opened_at'],row.get('closed_at') or 'Aberto',brl(row['opening_cents']),brl(row.get('expected_cents') or 0),brl(row.get('counted_cents') or 0),brl(row.get('difference_cents') or 0)))
        for label,action in [('Lançamento manual',entry),('Abrir caixa',open_cash),('Fechar caixa',close_cash),('Histórico de caixas',sessions)]:ttk.Button(cashbar,text=label,command=self.safe(action)).pack(side='left',padx=3)
        ttk.Button(balances,text='Abrir OS',command=self.safe(lambda:self.edit_order(self._selected(bt)))).pack(anchor='w');refresh()

    def page_reports(self):
        from .reports_ui import render_reports
        render_reports(self)

    def _printer_settings(self):
        with self.store.connect() as db:
            row=db.execute("SELECT value FROM meta WHERE key='printer_settings'").fetchone()
        return json.loads(row[0]) if row else {}

    def page_printers(self):
        from .service_documents import list_printers
        heading(self.body,'Impressoras e documentos','Associe cada formato a uma impressora instalada no sistema.')
        body=scroll_frame(self.body);settings=self._printer_settings();variables={}
        try:printers=list_printers()
        except (OSError,RuntimeError,ValueError) as exc:
            printers=[];ttk.Label(body,text='Não foi possível listar impressoras: '+str(exc),wraplength=600).pack(anchor='w')
        names=[p.get('name','') if isinstance(p,dict) else str(p) for p in printers]
        for paper in ('A4','80mm','58mm','ETIQUETA'):
            ttk.Label(body,text=paper).pack(anchor='w',pady=(15,5));var=tk.StringVar(value=settings.get(paper,''));variables[paper]=var
            ttk.Combobox(body,textvariable=var,values=['']+names,state='readonly').pack(fill='x')
        ttk.Label(body,text='Selecione uma impressora antes de imprimir. Instale impressoras e drivers pelo sistema operacional.',wraplength=600).pack(anchor='w',pady=18)
        def save():
            with self.store.connect() as db:db.execute('INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)',('printer_settings',json.dumps({k:v.get() for k,v in variables.items()})))
            messagebox.showinfo('Impressoras','Preferências salvas.',parent=self.root)
        ttk.Button(body,text='Salvar preferências',command=self.safe(save)).pack(anchor='w')
        ttk.Label(body,text='Emissão fiscal não configurada',foreground='#ffad56').pack(anchor='w',pady=20)
