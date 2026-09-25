import tkinter as tk
import sys

FONT = "Segoe UI" if sys.platform == "win32" else "Helvetica"
from tkinter import ttk, messagebox

NAVY='#020f22';TEAL='#008cff';BG='#051326';TEXT='#eef5ff';MUTED='#a3bddf'
CARD='#091e3a';BORDER='#203c60';CYAN='#00b7ff';INPUT='#04152e'

def styles(root):
    root.configure(bg=BG)
    # Native widgets used by OS notes/history share the same dark palette.
    for widget in ('Text','Entry','Listbox','Canvas','Toplevel'):
        root.option_add('*'+widget+'.background',INPUT if widget!='Toplevel' else BG)
    for widget in ('Text','Entry','Listbox'):
        root.option_add('*'+widget+'.foreground',TEXT)
        root.option_add('*'+widget+'.selectBackground','#076bd2')
        root.option_add('*'+widget+'.selectForeground','white')
        root.option_add('*'+widget+'.insertBackground',CYAN)
        root.option_add('*'+widget+'.highlightBackground',BORDER)
    root.option_add('*TCombobox*Listbox.background',INPUT)
    root.option_add('*TCombobox*Listbox.foreground',TEXT)
    s=ttk.Style(root);s.theme_use('clam')
    s.configure('.',font=(FONT,10),background=BG,foreground=TEXT)
    s.configure('TFrame',background=BG)
    s.configure('Card.TFrame',background=CARD)
    s.configure('Header.TFrame',background=NAVY)
    s.configure('Header.TLabel',background=NAVY,foreground=TEXT)
    s.configure('TLabel',background=BG,foreground=TEXT)
    s.configure('Card.TLabel',background=CARD,foreground=TEXT)
    s.configure('Title.TLabel',font=(FONT,24,'bold'))
    s.configure('Sub.TLabel',foreground=MUTED)
    s.configure('TButton',padding=(14,9),background='#132d50',foreground=TEXT,borderwidth=0,focuscolor=CYAN)
    s.map('TButton',background=[('active','#1c426f'),('disabled','#112139')],foreground=[('disabled','#7089a9')])
    for name,color,active in [('Primary','#007cff','#1498ff'),('Success','#008f70','#00aa85'),('Purple','#6536c4','#7e4bde')]:
        s.configure(name+'.TButton',background=color,foreground='white',font=(FONT,10,'bold'))
        s.map(name+'.TButton',background=[('active',active),('disabled','#183353')],foreground=[('disabled','#8298b3')])
    s.configure('TNotebook',background=BG,borderwidth=0,bordercolor=BG,lightcolor=BG,darkcolor=BG)
    s.configure('TNotebook.Tab',padding=(16,10),background='#112847',foreground=MUTED)
    s.map('TNotebook.Tab',background=[('selected','#006ee9'),('active','#17375e')],foreground=[('selected','white')])
    s.configure('TScrollbar',background='#29496f',troughcolor=BG,borderwidth=0,arrowsize=12,arrowcolor=MUTED)
    s.map('TScrollbar',background=[('active','#3673b3')])
    s.configure('TEntry',padding=8,fieldbackground=INPUT,foreground=TEXT,insertcolor=CYAN,bordercolor=BORDER,lightcolor=BORDER,darkcolor=BORDER)
    s.map('TEntry',bordercolor=[('focus',CYAN)],fieldbackground=[('readonly',CARD),('disabled',BG)],foreground=[('disabled',MUTED)])
    s.configure('TCombobox',padding=8,fieldbackground=INPUT,background=CARD,foreground=TEXT,arrowcolor=CYAN,bordercolor=BORDER)
    s.map('TCombobox',fieldbackground=[('readonly',INPUT)],foreground=[('readonly',TEXT)],selectbackground=[('readonly',INPUT)],selectforeground=[('readonly',TEXT)])
    s.configure('TCheckbutton',background=BG,foreground=MUTED,indicatorbackground=INPUT,indicatorforeground=CYAN)
    s.map('TCheckbutton',background=[('active',BG)],foreground=[('active',TEXT)],indicatorbackground=[('selected',TEAL)])
    s.configure('TLabelframe',background=BG,bordercolor=BORDER)
    s.configure('TLabelframe.Label',background=BG,foreground=CYAN)
    s.configure('TSeparator',background=BORDER)
    s.configure('Treeview',rowheight=38,background=INPUT,fieldbackground=INPUT,foreground=TEXT,borderwidth=0,bordercolor=BORDER,lightcolor=BORDER,darkcolor=BORDER)
    s.configure('Treeview.Heading',background='#0e2748',foreground=MUTED,font=(FONT,10,'bold'),padding=10,relief='flat')
    s.map('Treeview',background=[('selected','#075fb6')],foreground=[('selected','white')])
    s.map('Treeview.Heading',background=[('active','#173f6d')])
    rounded_button_styles(root,s)

def rounded_button_styles(root, style):
    from PIL import ImageTk
    from .surfaces import raster
    if not hasattr(root,'_button_art'):root._button_art=[]
    variants=[('TButton','#183356','#102642',BG),('Primary.TButton','#0088ff','#0064ff',BG),('Success.TButton','#00b08b','#00805f',CARD),('Purple.TButton','#8050d8','#552bbe',CARD),('Nav.TButton',NAVY,NAVY,NAVY),('NavSelected.TButton','#007cff','#0064fc',NAVY)]
    for name,top,bottom,base in variants:
        element='Premium.'+name
        if element not in style.element_names():
            pictures=[]
            for t,b,edge in [(top,bottom,top),('#238edf',bottom,CYAN),('#12263f','#12263f','#12263f'),(top,bottom,CYAN)]:
                im=raster(36,36,t,t,edge,12).copy()
                from PIL import Image
                backing=Image.new('RGBA',im.size,base);backing.alpha_composite(im)
                photo=ImageTk.PhotoImage(backing,master=root);pictures.append(photo);root._button_art.append(photo)
            style.element_create(element,'image',pictures[0],('disabled',pictures[2]),('pressed',pictures[1]),('active',pictures[1]),('focus',pictures[3]),border=13,sticky='nsew')
        style.layout(name,[(element,{'sticky':'nsew','children':[('Button.padding',{'sticky':'nsew','children':[('Button.label',{'sticky':'nsew'})]})]})])
    style.configure('Nav.TButton',anchor='w',padding=(10,3),foreground=MUTED,font=(FONT,10))
    style.configure('NavSelected.TButton',anchor='w',padding=(10,3),foreground='white',font=(FONT,10,'bold'))
    tab='Premium.Notebook.tab'
    if tab not in style.element_names():
        photos=[]
        for top,bottom,edge in [('#123052','#0b203c',BORDER),('#099bff','#0065ea',CYAN),('#184579','#123052',TEAL)]:
            photo=ImageTk.PhotoImage(raster(36,36,top,top,edge,12),master=root);photos.append(photo);root._button_art.append(photo)
        style.element_create(tab,'image',photos[0],('selected',photos[1]),('active',photos[2]),border=13,sticky='nsew')
    style.layout('TNotebook.Tab',[(tab,{'sticky':'nsew','children':[('Notebook.padding',{'sticky':'nsew','children':[('Notebook.label',{'sticky':'nsew'})]})]})])
    style.configure('TNotebook',tabmargins=(0,4,0,8),borderwidth=0)
    style.configure('TNotebook.Tab',padding=(12,2))
    style.map('TNotebook.Tab',expand=[('selected',(0,0,0,0))])
    style.configure('TButton',padding=(10,2))
    entry='Premium.Entry'
    if entry not in style.element_names():
        normal=ImageTk.PhotoImage(raster(36,36,INPUT,INPUT,BORDER,12),master=root)
        focused=ImageTk.PhotoImage(raster(36,36,INPUT,INPUT,CYAN,12),master=root)
        root._button_art.extend([normal,focused])
        style.element_create(entry,'image',normal,('focus',focused),border=13,sticky='nsew')
    style.layout('TEntry',[(entry,{'sticky':'nsew','children':[('Entry.padding',{'sticky':'nsew','children':[('Entry.textarea',{'sticky':'nsew'})]})]})])
    style.configure('TEntry',padding=(5,1))
    style.layout('TCombobox',[(entry,{'sticky':'nsew','children':[('Combobox.downarrow',{'side':'right','sticky':'ns'}),('Combobox.padding',{'sticky':'nsew','children':[('Combobox.textarea',{'sticky':'nsew'})]})]})])
    style.configure('TCombobox',padding=(5,1))

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


class TextValue:
    """Text control adapter used by forms with the same get/set contract as StringVar."""
    def __init__(self, widget):
        self.widget = widget

    def get(self):
        return self.widget.get('1.0', 'end-1c')

    def set(self, value):
        self.widget.delete('1.0', 'end')
        self.widget.insert('1.0', str(value or ''))
