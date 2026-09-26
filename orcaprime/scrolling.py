"""Mouse wheel routing for canvas forms, scoped to their own descendants."""
import tkinter as tk


def bind_mousewheel(canvas):
    top = canvas.winfo_toplevel()
    canvas._wheel_viewport = True

    def wheel(event):
        widget = event.widget
        # These widgets already handle the wheel through their class bindings.
        if widget.winfo_class() in ('Text', 'Listbox', 'Treeview', 'TCombobox', 'Spinbox', 'TSpinbox'):
            return
        while widget is not None:
            if getattr(widget, '_wheel_viewport', False):
                if widget is not canvas:
                    return
                break
            widget = getattr(widget, 'master', None)
        if widget is None or canvas.yview() == (0.0, 1.0):
            return
        delta = getattr(event, 'delta', 0)
        button = getattr(event, 'num', None)
        if button in (4, 5):
            units = -3 if button == 4 else 3
        elif delta:
            units = -max(1, abs(int(delta)) // 120) * (1 if delta > 0 else -1) * 3
        else:
            return
        canvas.yview_scroll(units, 'units')
        return 'break'

    bindings = [(sequence, top.bind(sequence, wheel, add='+'))
                for sequence in ('<MouseWheel>', '<Button-4>', '<Button-5>')]

    def cleanup(event):
        if event.widget is canvas:
            for sequence, callback in bindings:
                try:
                    top.unbind(sequence, callback)
                except tk.TclError:
                    pass
    canvas.bind('<Destroy>', cleanup, add='+')
