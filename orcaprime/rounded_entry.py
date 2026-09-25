"""Rounded native text inputs with a keyboard-accessible password toggle."""
import tkinter as tk
from tkinter import font as tkfont
from PIL import Image, ImageDraw, ImageTk
from .branding import line_icon
from .widgets import BG, FONT, TEXT, TEAL, MUTED, INPUT, BORDER, CYAN


class RoundedEntry(tk.Canvas):
    def __init__(self, parent, textvariable, password=False,placeholder=''):
        self.password = password
        self.revealed = False
        self.input_font = tkfont.Font(family=FONT, size=12)
        height = max(54, self.input_font.metrics('linespace') + 24)
        super().__init__(parent, height=height, bg=BG, highlightthickness=0,
                         borderwidth=0, takefocus=False)
        self.entry = tk.Entry(self, textvariable=textvariable, show='•' if password else '',
                              font=self.input_font, bg=INPUT, fg=TEXT, insertbackground=TEXT,
                              relief='flat', borderwidth=0, highlightthickness=0)
        self.entry_window = self.create_window(46, height / 2, anchor='w', window=self.entry)
        self.field_icon=line_icon(self,'lock' if password else 'customers',CYAN,24)
        self.icon_item=self.create_image(25,height/2,image=self.field_icon)
        self.hint=tk.Label(self,text=placeholder,font=self.input_font,bg=INPUT,fg=MUTED,bd=0)
        self.hint.bind('<Button-1>',lambda e:self.entry.focus_set())
        self.hint_window=self.create_window(46,height/2,anchor='w',window=self.hint,state='normal' if placeholder else 'hidden')
        self.variable=textvariable;self.placeholder=placeholder
        self.trace=textvariable.trace_add('write',lambda *_:self._draw())
        self.bind('<Destroy>',self._cleanup,add='+')
        self.toggle_button = None
        if password:
            self.icons = [self._eye(False), self._eye(True)]
            self.toggle_button = tk.Button(self, text='Mostrar', image=self.icons[0], compound='left',
                                          command=self.toggle, font=(FONT, 9), bg=INPUT, fg=MUTED,
                                          activebackground='#10325b', activeforeground=TEAL,
                                          relief='flat', borderwidth=0, cursor='hand2',
                                          highlightthickness=1, highlightbackground=INPUT,
                                          highlightcolor=TEAL, takefocus=True, padx=5)
            self.button_window = self.create_window(0, height / 2, anchor='e', window=self.toggle_button)
            self.toggle_button.bind('<Return>', lambda event: (self.toggle(), 'break')[1])
        self.bind('<Configure>', self._draw)
        self.entry.bind('<FocusIn>', self._draw)
        self.entry.bind('<FocusOut>', self._draw)
        self.bind('<Button-1>', lambda event: self.entry.focus_set())

    def _eye(self, crossed):
        scale = 3
        image = Image.new('RGBA', (24*scale, 24*scale))
        draw = ImageDraw.Draw(image)
        draw.ellipse((2*scale, 6*scale, 22*scale, 18*scale), outline=TEAL, width=2*scale)
        draw.ellipse((9*scale, 9*scale, 15*scale, 15*scale), fill=TEAL)
        if crossed:
            draw.line((3*scale, 3*scale, 21*scale, 21*scale), fill=TEAL, width=2*scale)
        return ImageTk.PhotoImage(image.resize((24, 24), Image.Resampling.LANCZOS), master=self)

    def _draw(self, event=None):
        width, height = self.winfo_width(), self.winfo_height()
        radius = 22
        self.delete('border')
        self.create_polygon(1+radius, 1, width-radius-1, 1, width-1, 1, width-1, 1+radius,
                            width-1, height-radius-1, width-1, height-1, width-radius-1, height-1,
                            radius+1, height-1, 1, height-1, 1, height-radius-1, 1, radius+1, 1, 1,
                            smooth=True, splinesteps=24, fill=INPUT,
                            outline=TEAL if self.entry.focus_get() == self.entry else '#087ee4',
                            width=2, tags='border')
        self.tag_lower('border')
        reserved = self.toggle_button.winfo_reqwidth() + 12 if self.toggle_button else 0
        self.itemconfigure(self.entry_window, width=max(20, width-60-reserved))
        self.coords(self.entry_window, 46, height/2)
        self.coords(self.hint_window,46,height/2)
        self.coords(self.icon_item,25,height/2)
        self.itemconfigure(self.hint_window,state='normal' if self.placeholder and not self.variable.get() and self.focus_get()!=self.entry else 'hidden')
        if self.toggle_button:
            self.coords(self.button_window, width-10, height/2)

    def _cleanup(self,event):
        if event.widget is self:
            self.variable.trace_remove('write',self.trace)

    def toggle(self):
        self.revealed = not self.revealed
        self.entry.configure(show='' if self.revealed else '•')
        self.toggle_button.configure(text='Ocultar' if self.revealed else 'Mostrar',
                                     image=self.icons[int(self.revealed)])
        self._draw()

    def focus_set(self):
        self.entry.focus_set()
