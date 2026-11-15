"""Exercise the actual desktop widgets on the Windows build runner."""
from openpost.shell import App

app = App()
app.withdraw()
app.demo()
app.select(0)
app.read()
assert app.selected().subject == "Подтверждение записи"
app.search.set("no-match-123")
assert app.selected() is None
app.search.set("")
assert app.selected() is not None
app.toggle_star()
app.set_filter("Важные")
assert app.selected().uid == "demo-clinic"
app.set_filter("Рассылки")
assert app.selected().uid == "demo-news"
app.set_filter("Люди")
assert app.selected().uid != "demo-news"
app.connect()
app.update()
for child in app.winfo_children():
    if child.winfo_class() == "Toplevel":
        child.destroy()
app.destroy()
print("GUI smoke check passed")
