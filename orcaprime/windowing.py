"""Screen-aware windows and background jobs without Tk calls from workers."""
import queue
import threading
import tkinter as tk


def fit_window(window, width=900, height=700):
    width=min(width,max(320,window.winfo_screenwidth()-60))
    height=min(height,max(240,window.winfo_screenheight()-110))
    window.geometry(f'{width}x{height}')
    window.minsize(min(width,540),min(height,360))


def maximize(window):
    try:window.state('zoomed')
    except tk.TclError:
        try:window.attributes('-zoomed',True)
        except tk.TclError:fit_window(window,window.winfo_screenwidth(),window.winfo_screenheight())


def background(widget, work, done):
    results=queue.Queue(maxsize=1)
    def worker():
        try:result=work();error=None
        except Exception as exc:result=None;error=exc
        results.put((result,error))
    timer=None
    def poll():
        nonlocal timer
        timer=None
        try:result,error=results.get_nowait()
        except queue.Empty:timer=widget.after(40,poll);return
        widget.unbind('<Destroy>',binding)
        done(result,error)
    def cleanup(event):
        nonlocal timer
        if event.widget is widget and timer is not None:
            widget.after_cancel(timer);timer=None
    binding=widget.bind('<Destroy>',cleanup,add='+')
    threading.Thread(target=worker,daemon=True).start()
    timer=widget.after(0,poll)
