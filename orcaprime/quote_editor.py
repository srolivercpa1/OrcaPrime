import copy
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date,timedelta,datetime
from .domain import calculate,brl,decimal_text,line_total,number
from .widgets import BG,heading,table

class QuoteEditor(tk.Toplevel):
    def __init__(self,parent,store,guard,on_saved,quote=None,duplicate=False):
        super().__init__(parent);self.title('OrçaPrime • Orçamento');self.geometry('1040x780');self.minsize(820,650)
        self.configure(bg=BG);self.transient(parent);self.store=store;self.guard=guard;self.on_saved=on_saved
        self.quote=copy.deepcopy(quote or {});self.id=None if duplicate else self.quote.get('id')
        self.source_id=self.quote.get('id') if duplicate else None
        self.items=copy.deepcopy(self.quote.get('items',[]));self.customers=store.list_customers();self.catalog=store.list_items()
        self.protocol('WM_DELETE_WINDOW',self.close)
        body=ttk.Frame(self,padding=20);body.pack(fill='both',expand=True)
        heading(body,'Novo orçamento' if not self.id else 'Editar '+self.quote['number'],'Preencha os itens e as condições. O PDF será gerado após salvar.')
        row=ttk.Frame(body);row.pack(fill='x')
        left=ttk.Frame(row);left.pack(side='left',fill='x',expand=True,padx=(0,15))
        ttk.Label(left,text='Cliente *').pack(anchor='w')
        self.customer=tk.StringVar();self.customer_choices={f"{c['id']} · {c['name']}":c['id'] for c in self.customers}
        ttk.Combobox(left,textvariable=self.customer,values=list(self.customer_choices),state='readonly').pack(fill='x',pady=5)
        for label,cid in self.customer_choices.items():
            if cid==self.quote.get('customer_id'): self.customer.set(label)
        right=ttk.Frame(row);right.pack(side='left');ttk.Label(right,text='Validade (DD/MM/AAAA) *').pack(anchor='w')
        valid=self.quote.get('valid_until',(date.today()+timedelta(days=15)).isoformat())
        self.valid=tk.StringVar(value=datetime.strptime(valid,'%Y-%m-%d').strftime('%d/%m/%Y'))
        ttk.Entry(right,textvariable=self.valid,width=20).pack(pady=5)
        catalogrow=ttk.Frame(body);catalogrow.pack(fill='x',pady=(12,8))
        ttk.Label(catalogrow,text='Catálogo:').pack(side='left',padx=(0,10));self.catalog_choice=tk.StringVar()
        select=ttk.Combobox(catalogrow,textvariable=self.catalog_choice,values=[f"{c['id']} · {c['description']}" for c in self.catalog],state='readonly');select.pack(side='left',fill='x',expand=True)
        select.bind('<<ComboboxSelected>>',self.from_catalog)
        ttk.Label(catalogrow,text='ou digite um item livre',style='Sub.TLabel').pack(side='left',padx=12)
        line=ttk.Frame(body);line.pack(fill='x');self.fields={}
        for key,label,width,default in [('description','Descrição *',44,''),('quantity','Quantidade *',10,'1'),('unit','Unidade',8,'un'),('price','Preço (R$) *',14,'0,00')]:
            frame=ttk.Frame(line);frame.pack(side='left',fill='x',expand=key=='description',padx=(0,8))
            ttk.Label(frame,text=label).pack(anchor='w');v=tk.StringVar(value=default);self.fields[key]=v
            ttk.Entry(frame,textvariable=v,width=width).pack(fill='x',pady=4)
        ttk.Button(line,text='Adicionar',style='Primary.TButton',command=self.add_item).pack(side='left',anchor='s',pady=4)
        self.tree=table(body,[('description','Descrição',390),('quantity','Qtd.',70),('unit','Un.',55),('price','Unitário',110),('total','Total',110)])
        actions=ttk.Frame(body);actions.pack(fill='x');ttk.Button(actions,text='Remover item selecionado',command=self.remove_item).pack(side='left')
        ttk.Label(actions,text='Desconto (R$):').pack(side='left',padx=(30,8));self.discount=tk.StringVar(value=decimal_text(self.quote.get('discount_cents',0)))
        ttk.Entry(actions,textvariable=self.discount,width=12).pack(side='left');self.total=ttk.Label(actions,font=('Segoe UI',16,'bold'));self.total.pack(side='right')
        self.discount.trace_add('write',lambda *_:self.refresh_total())
        notes=ttk.Frame(body);notes.pack(fill='x',pady=12)
        self.texts={}
        for key,label in [('terms','Condições de pagamento'),('notes','Observações')]:
            frame=ttk.Frame(notes);frame.pack(side='left',fill='both',expand=True,padx=(0,10));ttk.Label(frame,text=label).pack(anchor='w')
            text=tk.Text(frame,height=3,width=40,wrap='word',relief='solid',bd=1,font=('Segoe UI',10));text.pack(fill='x',pady=5)
            text.insert('1.0',self.quote.get(key,store.company().get('terms','') if key=='terms' else ''));self.texts[key]=text
        footer=ttk.Frame(body);footer.pack(fill='x');ttk.Button(footer,text='Cancelar',command=self.close).pack(side='right',padx=8)
        ttk.Button(footer,text='Salvar orçamento',style='Primary.TButton',command=self.save).pack(side='right')
        # Reserve the bottom controls before allowing the item table to expand.
        grid=self.tree.master
        for frame in (grid,actions,notes,footer):frame.pack_forget()
        footer.pack(side='bottom',fill='x')
        notes.pack(side='bottom',fill='x',pady=12)
        actions.pack(side='bottom',fill='x')
        grid.pack(fill='both',expand=True,pady=12)
        self.refresh();self.grab_set()
    def from_catalog(self,event=None):
        index=self.catalog_choice.get().split(' · ')[0]
        item=next((x for x in self.catalog if str(x['id'])==index),None)
        if item:
            self.fields['description'].set(item['description']);self.fields['unit'].set(item['unit']);self.fields['price'].set(decimal_text(item['price_cents']))
    def add_item(self):
        try:
            self.guard();item={k:v.get() for k,v in self.fields.items()}
            if not item['description'].strip(): raise ValueError('Informe a descrição do item.')
            item['total_cents']=line_total(item);self.items.append(item);self.refresh();self.fields['description'].set('');self.fields['quantity'].set('1')
        except ValueError as e: messagebox.showerror('Confira o item',str(e),parent=self)
    def remove_item(self):
        selected=self.tree.selection()
        if selected: self.items.pop(int(selected[0]));self.refresh()
    def refresh_total(self):
        try: total=calculate(self.items,self.discount.get())[2];self.total.configure(text='Total: '+brl(total))
        except ValueError: self.total.configure(text='Confira itens e desconto')
    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for n,item in enumerate(self.items):
            from .domain import money
            self.tree.insert('', 'end',iid=str(n),values=(item['description'],item['quantity'],item['unit'],brl(money(item['price'])),brl(line_total(item))))
        self.refresh_total()
    def save(self):
        try:
            self.guard()
            if self.customer.get() not in self.customer_choices: raise ValueError('Selecione um cliente.')
            try: valid=datetime.strptime(self.valid.get(),'%d/%m/%Y').date().isoformat()
            except ValueError: raise ValueError('Informe a validade no formato DD/MM/AAAA.') from None
            data={'customer_id':self.customer_choices[self.customer.get()],'valid_until':valid,'items':self.items,'discount':self.discount.get(),
                  'status':self.quote.get('status','RASCUNHO') if self.id else 'RASCUNHO',**{k:v.get('1.0','end-1c') for k,v in self.texts.items()}}
            self.store.save_quote(data,self.id,source_id=self.source_id);self.on_saved();self.destroy()
        except (ValueError,OSError) as e: messagebox.showerror('Confira o orçamento',str(e),parent=self)
    def close(self):
        if messagebox.askyesno('Fechar orçamento','Descartar as alterações que ainda não foram salvas?',parent=self): self.destroy()
