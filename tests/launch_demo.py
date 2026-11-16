"""Launch a synthetic mailbox for manual demonstrations; no email account is connected."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openpost.shell import App

app = App()
app.geometry("960x620+20+20")
app.demo()
app.select(0)
app.mainloop()
