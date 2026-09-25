"""Responsive premium dashboard components with real keyboard actions."""
import tkinter as tk
from tkinter import font
from .widgets import BG, FONT, TEAL, MUTED, CARD, BORDER, TEXT, CYAN
from .branding import line_icon
from .surfaces import surface


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
        bottom={'#159cff':'#052d66','#ff9e16':'#30251c','#10cba0':'#003d3c','#ae82ff':'#251b59'}.get(self.color,CARD)
        self.photo=surface(self,w,h,'#0a264c' if self.hover else '#061b37',bottom,self.color if self.focus_get()==self else BORDER,16,True)
        self.create_image(0,0,image=self.photo,anchor='nw')
        self.badge=surface(self,44,44,self.color,self.color,self.color,12)
        self.create_image(16,14,image=self.badge,anchor='nw')
        self.create_image(38,36,image=self.icon)
        self.create_text(18,64,text=str(self.value),font=self.number_font,fill=TEXT,anchor='nw')
        self.create_text(18,h-68,text=self.label,font=self.label_font,fill=self.color,anchor='nw',width=max(80,w-30))
        self.create_text(18,h-28,text=self.detail,font=(FONT,8),fill=MUTED,anchor='sw',width=max(80,w-40))
        self.create_line(18,h-15,w-18,h-15,fill=self.color,width=2)
    def invoke(self):return self.command()


class WelcomeBanner(tk.Canvas):
    """The exact static banner artwork from the user's approved visual reference."""
    def __init__(self,parent):
        from PIL import Image
        from .branding import asset_path
        super().__init__(parent,height=190,width=1,bg=BG,highlightthickness=0)
        with Image.open(asset_path('premium-banner.png')) as original:self.art=original.copy()
        self.bind('<Configure>',self.draw)
        self._size=None
    def draw(self,event=None):
        from PIL import Image,ImageTk
        w=max(1,self.winfo_width());h=max(1,round(w*self.art.height/self.art.width))
        if int(self.cget('height'))!=h:self.configure(height=h)
        if self._size==(w,h):return
        self._size=w,h
        self.photo=ImageTk.PhotoImage(self.art.resize((w,h),Image.Resampling.LANCZOS),master=self)
        self.delete('all');self.create_image(0,0,image=self.photo,anchor='nw')
