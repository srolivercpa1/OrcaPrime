"""Quote list with visible actions and an immutable delivered archive."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from .widgets import heading, table
from .domain import STATUSES, brl
from .quote_workflow import SERVICE_STATUSES, report_text
from .pdf import export_quote


def show_quotes(app):
    heading(app.body,'Orçamentos','Marque os atendimentos para atualizar o andamento. Consulte o histórico em Entregues.')
    bar=ttk.Frame(app.body);bar.pack(fill='x')
    search=tk.StringVar();ttk.Entry(bar,textvariable=search,width=24).pack(side='left',fill='x',expand=True)
    ttk.Button(bar,text='+ Novo',style='Primary.TButton',command=app.safe(app.new_quote)).pack(side='right',padx=(8,0))
    footer=ttk.Frame(app.body);footer.pack(side='bottom',fill='x',pady=(8,0))
    notebook=ttk.Notebook(app.body);notebook.pack(fill='both',expand=True,pady=(10,0))
    trees={};marked=set()
    for delivered,title in [(False,'Em atendimento'),(True,'Entregues')]:
        frame=ttk.Frame(notebook);notebook.add(frame,text=title)
        tree=table(frame,[('mark','☐',44),('n','Número',120),('c','Cliente',175),('e','Aparelho',145),('s','Andamento',125),('commercial','Orçamento',105),('delivery','Entrega',145),('t','Total',110)])
        tree.column('mark',width=44,minwidth=44,stretch=False);trees[delivered]=tree
    app.quote_trees=trees;app.quote_tabs=notebook
    def is_delivered():return notebook.index(notebook.select())==1
    def current():return trees[is_delivered()]
    count=tk.StringVar(value='Nenhum atendimento marcado')
    ttk.Label(footer,textvariable=count,style='Sub.TLabel').grid(row=0,column=0,columnspan=4,sticky='w',pady=(0,4))
    def update_marks():
        tree=current()
        for row in tree.get_children():tree.set(row,'mark','☑' if int(row) in marked else '☐')
        count.set(f'{len(marked)} atendimento(s) marcado(s)')
    def toggle_all():
        ids={int(row) for row in current().get_children()}
        marked.clear() if marked==ids else marked.update(ids)
        update_marks()
    def toggle(event):
        tree=current();row=tree.identify_row(event.y)
        if row and tree.identify_column(event.x)=='#1':
            id_=int(row)
            marked.remove(id_) if id_ in marked else marked.add(id_)
            tree.selection_set(row);tree.focus(row);update_marks();return 'break'
    def keyboard_toggle(event):
        row=current().focus()
        if row:
            id_=int(row);marked.remove(id_) if id_ in marked else marked.add(id_);update_marks()
        return 'break'
    def selected():
        ids=marked or {int(row) for row in current().selection()}
        if len(ids)!=1:raise ValueError('Selecione somente um atendimento para esta ação.')
        return app.store.get_quote(next(iter(ids)))
    def refresh(*_):
        marked.clear();tree=current();tree.delete(*tree.get_children())
        for q in app.store.list_quotes(search.get(),delivered=is_delivered()):
            delivery=q.get('delivered_at','')
            if delivery:
                from datetime import datetime
                delivery=datetime.fromisoformat(delivery).strftime('%d/%m/%Y %H:%M')
            tree.insert('','end',iid=str(q['id']),values=('☐',q['number'],q['customer']['name'],q.get('equipment',''),SERVICE_STATUSES[q.get('service_status','AGUARDANDO')],q['status'],delivery,brl(q['total_cents'])))
        update_marks()
        edit_button.configure(state='disabled' if is_delivered() else 'normal')
        change_button.configure(state='disabled' if is_delivered() else 'normal')
        status_box.configure(state='disabled' if is_delivered() else 'readonly')
    def report():
        from .windowing import fit_window
        q=selected();win=tk.Toplevel(app.root);win.title('Relatório — '+q['number']);fit_window(win,800,700)
        actions=ttk.Frame(win,padding=10);actions.pack(side='bottom',fill='x')
        text=tk.Text(win,wrap='word');scroll=ttk.Scrollbar(win,command=text.yview);scroll.pack(side='right',fill='y');text.pack(fill='both',expand=True);text.configure(yscrollcommand=scroll.set)
        text.insert('1.0',report_text(q));text.configure(state='disabled')
        def save_pdf():
            app.guard();path=filedialog.asksaveasfilename(parent=win,defaultextension='.pdf',initialfile='Relatorio-'+q['number']+'.pdf',filetypes=[('PDF','*.pdf')])
            if path:export_quote(path,q,app.store.company(),report=True)
        ttk.Button(actions,text='Salvar relatório PDF',command=app.safe(save_pdf)).pack(side='left')
        ttk.Button(actions,text='Fechar',command=win.destroy).pack(side='right')
    def pdf():
        q=selected();path=filedialog.asksaveasfilename(parent=app.root,defaultextension='.pdf',initialfile='Orcamento-'+q['number']+'.pdf',filetypes=[('PDF','*.pdf')])
        if path:export_quote(path,q,app.store.company())
    edit_button=ttk.Button(footer,text='Editar',command=app.safe(lambda:app.new_quote(selected())))
    edit_button.grid(row=1,column=0,sticky='ew',padx=(0,4),pady=3)
    ttk.Button(footer,text='Duplicar',command=app.safe(lambda:app.new_quote(selected(),True))).grid(row=1,column=1,sticky='ew',padx=(4,0),pady=3)
    ttk.Button(footer,text='Exportar PDF',command=app.safe(pdf)).grid(row=1,column=2,sticky='ew',padx=(0,4),pady=3)
    ttk.Button(footer,text='Relatório',command=app.safe(report)).grid(row=1,column=3,sticky='ew',padx=(4,0),pady=3)
    options={**{'Aparelho: '+label:('service',key) for key,label in SERVICE_STATUSES.items()},**{'Orçamento: '+status:('commercial',status) for status in STATUSES}}
    status=tk.StringVar(value='Aparelho: Em andamento')
    status_box=ttk.Combobox(footer,textvariable=status,values=tuple(options),state='readonly',width=20);status_box.grid(row=2,column=0,columnspan=2,sticky='ew',padx=(0,4),pady=3)
    def change():
        ids=sorted(marked)
        if not ids:raise ValueError('Marque a caixa ao lado dos atendimentos que deseja alterar.')
        mode,value=options[status.get()]
        if mode=='service':
            note=simpledialog.askstring('Atualizar andamento','Observações / responsável pela retirada (opcional):',parent=app.root)
            if note is None:return
            if value=='ENTREGUE' and not messagebox.askyesno('Confirmar entrega',f'Marcar {len(ids)} atendimento(s) como entregue(s)? Eles irão para Entregues, com data e histórico preservados e somente leitura.',parent=app.root):return
            app.guard();app.store.set_service_status(ids,value,note,app.actor.get('name',''))
        else:
            for id_ in ids:app.store.set_status(id_,value)
        refresh()
    change_button=ttk.Button(footer,text='Aplicar aos marcados',command=app.safe(change));change_button.grid(row=2,column=2,columnspan=2,sticky='ew',padx=(4,0),pady=3)
    footer.columnconfigure((0,1,2,3),weight=1,uniform='actions')
    for tree in trees.values():
        tree.heading('mark',command=toggle_all);tree.bind('<Button-1>',toggle);tree.bind('<space>',keyboard_toggle)
        tree.bind('<Double-1>',lambda e:app.safe(report if is_delivered() else lambda:app.new_quote(selected()))())
    search.trace_add('write',refresh);notebook.bind('<<NotebookTabChanged>>',refresh);refresh()
