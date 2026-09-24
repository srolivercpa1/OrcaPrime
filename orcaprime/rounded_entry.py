"""Rounded native text inputs with a keyboard-accessible password toggle."""
import tkinter as tk
from tkinter import font as tkfont
from PIL import Image, ImageDraw, ImageTk
from .widgets import BG, FONT, TEXT, TEAL, MUTED


class RoundedEntry(tk.Canvas):
    def __init__(self, parent, textvariable, password=False):
        self.password = password
        self.revealed = False
        self.input_font = tkfont.Font(family=FONT, size=11)
        height = max(46, self.input_font.metrics('linespace') + 24)
        super().__init__(parent, height=height, bg=BG, highlightthickness=0,
                         borderwidth=0, takefocus=False)
        self.entry = tk.Entry(self, textvariable=textvariable, show='•' if password else '',
                              font=self.input_font, bg='white', fg=TEXT, insertbackground=TEXT,
                              relief='flat', borderwidth=0, highlightthickness=0)
        self.entry_window = self.create_window(14, height / 2, anchor='w', window=self.entry)
        self.toggle_button = None
        if password:
            self.icons = [self._eye(False), self._eye(True)]
            self.toggle_button = tk.Button(self, text='Mostrar', image=self.icons[0], compound='left',
                                          command=self.toggle, font=(FONT, 9), bg='white', fg=MUTED,
                                          activebackground='#e8f4f2', activeforeground=TEAL,
                                          relief='flat', borderwidth=0, cursor='hand2',
                                          highlightthickness=1, highlightbackground='white',
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
        radius = 12
        self.delete('border')
        self.create_polygon(1+radius, 1, width-radius-1, 1, width-1, 1, width-1, 1+radius,
                            width-1, height-radius-1, width-1, height-1, width-radius-1, height-1,
                            radius+1, height-1, 1, height-1, 1, height-radius-1, 1, radius+1, 1, 1,
                            smooth=True, splinesteps=24, fill='white',
                            outline=TEAL if self.entry.focus_get() == self.entry else '#cbd5e1',
                            width=2, tags='border')
        self.tag_lower('border')
        reserved = self.toggle_button.winfo_reqwidth() + 12 if self.toggle_button else 0
        self.itemconfigure(self.entry_window, width=max(20, width-28-reserved))
        self.coords(self.entry_window, 14, height/2)
        if self.toggle_button:
            self.coords(self.button_window, width-10, height/2)

    def toggle(self):
        self.revealed = not self.revealed
        self.entry.configure(show='' if self.revealed else '•')
        self.toggle_button.configure(text='Ocultar' if self.revealed else 'Mostrar',
                                     image=self.icons[int(self.revealed)])
        self._draw()

    def focus_set(self):
        self.entry.focus_set()
