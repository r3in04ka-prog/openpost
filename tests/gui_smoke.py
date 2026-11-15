"""Exercise the actual desktop widgets on the Windows build runner."""
from openpost.app import App

app = App()
app.withdraw()
app.demo()
app.list.selection_set("0")
app.read()
assert "OpenPost" in app.body.get("1.0", "end")
app.search.set("no-match-123")
assert not app.list.get_children()
app.search.set("")
assert len(app.list.get_children()) == 1
app.destroy()
print("GUI smoke check passed")
