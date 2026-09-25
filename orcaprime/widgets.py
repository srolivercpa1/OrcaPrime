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
    s.configure('TNotebook',background=BG,borderwidth=0)
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
    s.configure('Treeview',rowheight=38,background=INPUT,fieldbackground=INPUT,foreground=TEXT,borderwidth=0)
    s.configure('Treeview.Heading',background='#0e2748',foreground=MUTED,font=(FONT,10,'bold'),padding=10,relief='flat')
    s.map('Treeview',background=[('selected','#075fb6')],foreground=[('selected','white')])
    s.map('Treeview.Heading',background=[('active','#173f6d')])
    rounded_button_styles(root,s)

def rounded_button_styles(root, style):
    from PIL import Image, ImageDraw, ImageTk
    if not hasattr(root,'_button_art'):root._button_art=[]
    for name,color,active in [('TButton','#142f53','#1d4576'),('Primary.TButton','#007cff','#1398ff'),('Success.TButton','#008f70','#00aa85'),('Purple.TButton','#6536c4','#7e4bde')]:
        element='Premium.'+name
        if element not in style.element_names():
            pictures=[]
            for fill,outline in [(color,color),(active,active),('#12263f','#12263f'),(color,CYAN)]:
                im=Image.new('RGB',(160,160),BG);draw=ImageDraw.Draw(im)
                draw.rounded_rectangle((2,2,157,157),radius=42,fill=fill,outline=outline,width=6)
                photo=ImageTk.PhotoImage(im.resize((40,40),Image.Resampling.LANCZOS),master=root)
                pictures.append(photo);root._button_art.append(photo)
            style.element_create(element,'image',pictures[0],('disabled',pictures[2]),('pressed',pictures[1]),('active',pictures[1]),('focus',pictures[3]),border=12,sticky='nsew')
        style.layout(name,[(element,{'sticky':'nsew','children':[('Button.padding',{'sticky':'nsew','children':[('Button.label',{'sticky':'nsew'})]})]})])

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
