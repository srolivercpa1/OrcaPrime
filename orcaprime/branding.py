"""Shared assets for source and PyInstaller builds."""
from pathlib import Path
import sys
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw


def asset_path(name):
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent)) / 'assets' / name


def brand_image(master, size=64):
    with Image.open(asset_path('brand.png')) as source:
        return ImageTk.PhotoImage(source.resize((size, size), Image.Resampling.LANCZOS), master=master)


def apply_icon(window):
    if sys.platform=='win32':
        window.iconbitmap(str(asset_path('orcaprime-premium-r2.ico')))
    window._brand_icon = brand_image(window, 64)
    window.iconphoto(True, window._brand_icon)


def brand_header(parent, bg, size=48):
    frame = tk.Frame(parent, bg=bg)
    picture = brand_image(frame, size)
    logo = tk.Label(frame, image=picture, bg=bg, bd=0)
    logo.image = picture
    logo.pack(side='left', padx=(0,10))
    from .widgets import FONT
    words = tk.Frame(frame, bg=bg); words.pack(side='left')
    name = tk.Frame(words, bg=bg); name.pack(anchor='w')
    tk.Label(name,text='Orça',font=(FONT,19,'bold'),fg='#f4f8ff',bg=bg,padx=0).pack(side='left')
    tk.Label(name,text='Prime',font=(FONT,19,'bold'),fg='#00afff',bg=bg,padx=0).pack(side='left')
    tk.Label(words,text='GESTÃO DA ASSISTÊNCIA',font=(FONT,7),fg='#9ab5d9',bg=bg).pack(anchor='w')
    return frame


def line_icon(master, kind, color='#aec5e8', size=22):
    """Small, consistent navigation pictograms drawn independently of system fonts."""
    im=Image.new('RGBA',(72,72));d=ImageDraw.Draw(im);c=color
    if kind == 'lock':
        d.arc((22,8,50,44),0,180,fill=c,width=5);d.arc((22,8,50,44),180,360,fill=c,width=5);d.rounded_rectangle((15,29,57,63),radius=6,fill=c);d.line((36,40,36,52),fill='#061a34',width=5)
    elif kind in ('customers','users'):
        d.ellipse((25,7,47,29),outline=c,width=5);d.arc((13,34,59,72),180,360,fill=c,width=5);d.line((13,53,59,53),fill=c,width=5)
    elif kind in ('dashboard','company'):
        d.line((9,33,36,10,63,33),fill=c,width=5);d.rectangle((18,32,54,61),outline=c,width=5);d.rectangle((30,43,42,61),outline=c,width=4)
    elif kind in ('stock','catalog','suppliers'):
        d.polygon((12,22,36,10,60,22,60,51,36,63,12,51),outline=c,width=4);d.line((12,22,36,35,60,22),fill=c,width=4);d.line((36,35,36,63),fill=c,width=4)
    elif kind in ('orders','printers'):
        d.line((22,53,48,27),fill=c,width=9);d.arc((36,7,65,36),35,285,fill=c,width=6);d.ellipse((12,48,26,62),outline=c,width=4)
    elif kind in ('warranties','backup'):
        d.polygon((36,9,59,18,56,45,36,63,16,45,13,18),outline=c,width=4);d.line((24,35,33,44,49,27),fill=c,width=5)
    else:
        d.rounded_rectangle((16,10,56,62),radius=5,outline=c,width=4)
        for y in (25,36,47):d.line((26,y,46,y),fill=c,width=4)
    return ImageTk.PhotoImage(im.resize((size,size),Image.Resampling.LANCZOS),master=master)
