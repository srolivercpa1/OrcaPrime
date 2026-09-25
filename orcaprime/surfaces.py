"""Antialiased rounded surfaces, shared by cards, panels and native ttk tabs."""
from functools import lru_cache
from PIL import Image, ImageDraw, ImageColor, ImageTk
import tkinter as tk
from .widgets import BG, CARD, BORDER


@lru_cache(maxsize=48)
def raster(width,height,top,bottom,border,radius=16,facets=False):
    scale=2;w=max(4,width)*scale;h=max(4,height)*scale
    start=ImageColor.getrgb(top);end=ImageColor.getrgb(bottom)
    im=Image.new('RGBA',(w,h));d=ImageDraw.Draw(im)
    for y in range(h):
        t=y/max(1,h-1);c=tuple(round(a+(b-a)*t) for a,b in zip(start,end))
        d.line((0,y,w,y),fill=c)
    if facets:
        overlay=Image.new('RGBA',(w,h));o=ImageDraw.Draw(overlay)
        o.polygon((w*.82,0,w,0,w,h*.55,w*.52,h,w*.26,h),fill=(40,108,210,25))
        im=Image.alpha_composite(im,overlay)
    mask=Image.new('L',(w,h));md=ImageDraw.Draw(mask)
    md.rounded_rectangle((1,1,w-2,h-2),radius=radius*scale,fill=255)
    im.putalpha(mask);d=ImageDraw.Draw(im)
    d.rounded_rectangle((1,1,w-2,h-2),radius=radius*scale,outline=border,width=2)
    return im.resize((max(4,width),max(4,height)),Image.Resampling.LANCZOS)


def surface(master,w,h,top,bottom,border,radius=16,facets=False):
    return ImageTk.PhotoImage(raster(int(w),int(h),top,bottom,border,radius,facets),master=master)


class RoundPanel(tk.Canvas):
    def __init__(self,parent,padding=16):
        super().__init__(parent,bg=BG,highlightthickness=0,bd=0,width=1)
        self.padding=padding
        self.content=tk.Frame(self,bg=CARD)
        self.window=self.create_window(padding,padding,anchor='nw',window=self.content)
        self.content.bind('<Configure>',self.fit)
        self.bind('<Configure>',self.draw)
        self._size=None
    def fit(self,event=None):
        needed=self.content.winfo_reqheight()+2*self.padding
        if self.winfo_pixels(self.cget('height'))!=needed:self.configure(height=needed)
    def draw(self,event=None):
        w,h=self.winfo_width(),self.winfo_height()
        self.itemconfigure(self.window,width=max(1,w-2*self.padding))
        if self._size!=(w,h):
            self._size=w,h;self.photo=surface(self,w,h,CARD,CARD,BORDER,16)
            self.delete('surface');self.create_image(0,0,image=self.photo,anchor='nw',tags='surface');self.tag_lower('surface')
