"""Capture the actual application using synthetic demo content on CI."""
from PIL import ImageGrab
from openpost.app import App

app = App()
app.geometry("960x600+10+10")
app.demo()
app.list.selection_set("0")
app.read()
app.update()

def capture():
    app.update()
    x, y = app.winfo_rootx(), app.winfo_rooty()
    ImageGrab.grab(bbox=(x, y, x + app.winfo_width(), y + app.winfo_height())).save("openpost-preview.png")
    app.destroy()

app.after(1500, capture)
app.mainloop()
