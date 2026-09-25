"""Responsive premium dashboard components with real keyboard actions."""
import tkinter as tk
from tkinter import font
from .widgets import BG, FONT, TEAL, MUTED, CARD, BORDER, TEXT, CYAN
from .branding import line_icon


def rounded(canvas, w, h, fill, outline, tag=None):
    r=20
    return canvas.create_polygon(r,2,w-r,2,w-2,2,w-2,r,w-2,h-r,w-2,h-2,w-r,h-2,
        r,h-2,2,h-2,2,h-r,2,r,2,2,smooth=True,splinesteps=32,fill=fill,outline=outline,width=1,tags=tag or ())


class MetricCard(tk.Canvas):
    def __init__(self,parent,value,label,color,command,detail='',icon='orders'):
        self.value,self.label,self.color,self.command,self.detail=value,label,color,command,detail
        self.number_font=font.Font(family=FONT,size=24,weight='bold')
        self.label_font=font.Font(family=FONT,size=9,weight='bold')
        height=max(188,self.number_font.metrics('linespace')+self.label_font.metrics('linespace')*3+100)
        super().__init__(parent,bg=BG,width=1,height=height,highlightthickness=0,takefocus=True,cursor='hand2')
        self.icon=line_icon(self,icon,'white',24);self.hover=False
        self.bind('<Configure>',self.draw);self.bind('<FocusIn>',self.draw);self.bind('<FocusOut>',self.draw)
        self.bind('<Enter>',lambda e:self.highlight(True));self.bind('<Leave>',lambda e:self.highlight(False))
        self.bind('<Button-1>',lambda e:self.invoke())
        self.bind('<Return>',lambda e:(self.invoke(),'break')[1]);self.bind('<space>',lambda e:(self.invoke(),'break')[1])
    def highlight(self,active):
        self.hover=active;self.draw()
    def draw(self,event=None):
        self.delete('all');w,h=self.winfo_width(),self.winfo_height()
        rounded(self,w,h,'#0d2b50' if self.hover else CARD,self.color if self.focus_get()==self else BORDER)
        self.create_polygon(w-2,h*.45,w-2,h-12,w-14,h-2,w*.35,h-2,fill='#0c2948',outline='')
        self.create_rectangle(18,16,58,56,fill=self.color,outline='')
        self.create_image(38,36,image=self.icon)
        self.create_text(18,64,text=str(self.value),font=self.number_font,fill=TEXT,anchor='nw')
        self.create_text(18,h-68,text=self.label,font=self.label_font,fill=self.color,anchor='nw',width=max(80,w-30))
        self.create_text(18,h-28,text=self.detail,font=(FONT,8),fill=MUTED,anchor='sw',width=max(80,w-40))
        self.create_line(18,h-15,w-18,h-15,fill=self.color,width=2)
    def invoke(self):return self.command()


class WelcomeBanner(tk.Canvas):
    def __init__(self,parent):
        super().__init__(parent,height=200,width=1,bg=BG,highlightthickness=0)
        self.bind('<Configure>',self.draw)
    def draw(self,event=None):
        self.delete('all');w,h=self.winfo_width(),self.winfo_height()
        rounded(self,w,h,'#06244d','#15558c')
        self.create_polygon(w*.6,2,w-20,2,w*.8,h-2,w*.42,h-2,fill='#082d64',outline='')
        title_size=23 if w>600 else 19
        self.create_text(22,20,text='SUA ASSISTÊNCIA SEMPRE EM DIA',font=(FONT,9),fill=MUTED,anchor='nw')
        self.create_text(22,47,text='Mais controle.',font=(FONT,title_size,'bold'),fill=TEXT,anchor='nw')
        self.create_text(22,84,text='Mais resultados.',font=(FONT,title_size,'bold'),fill=CYAN,anchor='nw')
        self.create_text(22,132,text='Organize seus atendimentos e acompanhe\ncada etapa da ordem de serviço.',font=(FONT,10),fill=MUTED,anchor='nw',width=max(200,w*.55))
        if w>610:
            x=w-210;y=46
            self.create_polygon(x+35,y,x+178,y+14,x+156,y+118,x+12,y+100,fill='#07356b',outline=TEAL,width=2)
            self.create_polygon(x+42,y+10,x+168,y+22,x+149,y+104,x+24,y+90,fill='#061a37',outline='#0b6bc4')
            self.create_polygon(x+12,y+100,x+156,y+118,x+195,y+145,x-20,y+121,fill='#0b3970',outline=TEAL,width=2)
            self.create_line(x+71,y+82,x+115,y+38,fill=CYAN,width=12,capstyle='round')
            self.create_arc(x+94,y+17,x+132,y+55,start=30,extent=280,style='arc',outline=CYAN,width=8)
