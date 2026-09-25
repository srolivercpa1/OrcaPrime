"""Keyboard-accessible dashboard cards rendered with the application's palette."""
import tkinter as tk
from tkinter import font
from .widgets import BG, FONT, TEAL, MUTED


class MetricCard(tk.Canvas):
    def __init__(self, parent, value, label, color, command):
        self.value, self.label, self.color, self.command = value, label, color, command
        self.number_font = font.Font(family=FONT, size=30, weight='bold')
        self.label_font = font.Font(family=FONT, size=10)
        height = max(142, self.number_font.metrics('linespace') + self.label_font.metrics('linespace')*2 + 50)
        super().__init__(parent, bg=BG, height=height, highlightthickness=0, takefocus=True, cursor='hand2')
        self.hover = False
        self.bind('<Configure>', self.draw)
        self.bind('<FocusIn>', self.draw)
        self.bind('<FocusOut>', self.draw)
        self.bind('<Enter>', lambda e: self.highlight(True))
        self.bind('<Leave>', lambda e: self.highlight(False))
        self.bind('<Button-1>', lambda e: self.invoke())
        self.bind('<Return>', lambda e: (self.invoke(), 'break')[1])
        self.bind('<space>', lambda e: (self.invoke(), 'break')[1])

    def highlight(self, active):
        self.hover = active
        self.draw()

    def draw(self, event=None):
        self.delete('all')
        w, h, r = self.winfo_width(), self.winfo_height(), 22
        self.create_polygon(r,2,w-r,2,w-2,2,w-2,r,w-2,h-r,w-2,h-2,w-r,h-2,
                            r,h-2,2,h-2,2,h-r,2,r,2,2,smooth=True,splinesteps=32,
                            fill='#f8fffd' if self.hover else 'white',
                            outline=TEAL if self.focus_get()==self else '#e1e8f0',width=2)
        self.create_line(22,24,44,24,fill=self.color,width=4,capstyle='round')
        self.create_text(22,38,text=str(self.value),font=self.number_font,fill=self.color,anchor='nw')
        self.create_text(22,h-24,text=self.label,font=self.label_font,fill=MUTED,anchor='sw',width=max(80,w-55))
        self.create_text(w-26,24,text='›',font=(FONT,19),fill=self.color)

    def invoke(self):
        return self.command()
