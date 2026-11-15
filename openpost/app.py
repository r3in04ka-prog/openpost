"""Tk interface; worker threads communicate through a queue."""
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from .mail import Account, Letter, fetch_inbox, send_message


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OpenPost · Почта под вашим контролем")
        self.geometry("1180x760")
        self.minsize(860, 560)
        self.account = None
        self.letters = []
        self.events = queue.Queue()
        self.busy = False
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TButton", padding=9)
        style.configure("Treeview", rowheight=34, font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 24, "bold"))
        top = ttk.Frame(self, padding=20)
        top.pack(fill="x")
        ttk.Label(top, text="OpenPost", style="Title.TLabel").pack(side="left")
        for text, action in [("Подключить почту", self.connect), ("Демо", self.demo),
                             ("Обновить", self.refresh), ("Написать", self.compose)]:
            ttk.Button(top, text=text, command=action).pack(side="right", padx=4)
        self.status = tk.StringVar(value="Локальный почтовый клиент · Подключите аккаунт или откройте демо")
        ttk.Label(self, textvariable=self.status, padding=(20, 8)).pack(fill="x")
        self.search = tk.StringVar()
        bar = ttk.Frame(self, padding=(20, 8))
        bar.pack(fill="x")
        ttk.Label(bar, text="Поиск по загруженным письмам").pack(side="left", padx=(0, 10))
        ttk.Entry(bar, textvariable=self.search).pack(side="left", fill="x", expand=True)
        self.search.trace_add("write", lambda *_: self.render())
        panes = ttk.Panedwindow(self, orient="horizontal")
        panes.pack(fill="both", expand=True, padx=20, pady=12)
        left = ttk.Frame(panes)
        self.list = ttk.Treeview(left, columns=("from", "subject"), show="headings", selectmode="browse")
        self.list.heading("from", text="Отправитель")
        self.list.heading("subject", text="Тема")
        self.list.column("from", width=180)
        self.list.column("subject", width=240)
        scroll = ttk.Scrollbar(left, command=self.list.yview)
        self.list.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.list.pack(fill="both", expand=True)
        self.list.bind("<<TreeviewSelect>>", self.read)
        right = ttk.Frame(panes)
        ttk.Button(right, text="Ответить", command=self.reply).pack(anchor="e", pady=(0, 8))
        self.body = tk.Text(right, wrap="word", font=("Segoe UI", 11), padx=18, pady=18, relief="flat", state="disabled")
        body_scroll = ttk.Scrollbar(right, command=self.body.yview)
        self.body.configure(yscrollcommand=body_scroll.set)
        body_scroll.pack(side="right", fill="y")
        self.body.pack(fill="both", expand=True)
        panes.add(left, weight=1)
        panes.add(right, weight=2)
        self.after(100, self.poll)

    def work(self, action, success):
        if self.busy:
            messagebox.showinfo("OpenPost", "Дождитесь завершения текущей операции.", parent=self)
            return
        self.busy = True
        self.status.set("Выполняется операция…")
        def run():
            try:
                self.events.put((success, action(), None))
            except Exception:
                # Never show server responses: they may contain sensitive information.
                self.events.put((success, None, "Операция не завершена. Проверьте сеть, серверы и пароль приложения. Если это отправка, проверьте доставку перед повтором."))
        threading.Thread(target=run, daemon=True).start()

    def poll(self):
        try:
            callback, result, error = self.events.get_nowait()
            self.busy = False
            if error:
                self.status.set("Ошибка подключения или передачи")
                messagebox.showerror("OpenPost", error, parent=self)
            else:
                callback(result)
        except queue.Empty:
            pass
        self.after(100, self.poll)

    def connect(self):
        if self.busy:
            return
        win = tk.Toplevel(self)
        win.title("Подключение аккаунта")
        win.transient(self)
        win.grab_set()
        fields = []
        for row, (label, default) in enumerate([("Email", ""), ("Пароль приложения", ""),
                ("IMAP сервер (TLS, 993)", ""), ("SMTP сервер", ""), ("SMTP порт (465 или 587)", "465")]):
            ttk.Label(win, text=label).grid(row=row, column=0, padx=15, pady=10, sticky="w")
            entry = ttk.Entry(win, width=36, show="•" if row == 1 else "")
            entry.insert(0, default)
            entry.grid(row=row, column=1, padx=15, pady=10)
            fields.append(entry)
        ttk.Label(win, text="Пароль не сохраняется. OAuth пока не поддерживается.").grid(row=5, columnspan=2, padx=15, pady=10)
        def save():
            try:
                values = [field.get() for field in fields]
                account = Account(*values[:4], int(values[4]))
                account.validate()
            except ValueError as error:
                messagebox.showerror("Настройки", str(error), parent=win)
                return
            win.destroy()
            def connected(letters):
                self.account = account
                self.loaded(letters)
            self.work(lambda: fetch_inbox(account), connected)
        ttk.Button(win, text="Подключить", command=save).grid(row=6, columnspan=2, pady=15)

    def loaded(self, letters):
        self.letters = letters
        self.render()
        self.status.set(f"Входящие · Загружено: {len(letters)} · Последние 50 писем")

    def refresh(self):
        if not self.account:
            messagebox.showinfo("OpenPost", "Сначала подключите почту.", parent=self)
            return
        account = self.account
        self.work(lambda: fetch_inbox(account), self.loaded)

    def render(self):
        self.list.delete(*self.list.get_children())
        self.show_body("")
        query = self.search.get().casefold()
        for index, letter in enumerate(self.letters):
            if query in f"{letter.sender} {letter.subject} {letter.body}".casefold():
                self.list.insert("", "end", iid=str(index), values=(letter.sender, letter.subject))

    def selected(self):
        selection = self.list.selection()
        return self.letters[int(selection[0])] if selection else None

    def show_body(self, text):
        self.body.configure(state="normal")
        self.body.delete("1.0", "end")
        self.body.insert("1.0", text)
        self.body.configure(state="disabled")

    def read(self, *_):
        letter = self.selected()
        if letter:
            self.show_body(f"{letter.subject}\n\nОт: {letter.sender}\nДата: {letter.date}\n\n{letter.body}")

    def demo(self):
        if self.busy:
            return
        self.account = None
        self.loaded([Letter("demo", "Команда OpenPost <hello@example.org>", "Ваша почта. Ваши правила.",
            "Демонстрационное письмо", "Добро пожаловать в OpenPost!\n\nПодключите аккаунт через IMAP и SMTP, чтобы читать и отправлять письма.\n\nДемо не обращается к вашей почте. HTML не выполняется, внешние картинки не загружаются.\n\nИсходный код открыт под лицензией MIT.")])
        self.status.set("Деморежим · Отправка отключена")

    def reply(self):
        letter = self.selected()
        if letter:
            self.compose(letter)

    def compose(self, letter=None):
        if not self.account:
            messagebox.showinfo("OpenPost", "Для отправки подключите почту.", parent=self)
            return
        account = self.account
        win = tk.Toplevel(self)
        win.title("Новое письмо")
        win.geometry("650x520")
        win.transient(self)
        win.grab_set()
        ttk.Label(win, text="Кому").pack(anchor="w", padx=15, pady=(15, 3))
        recipient = ttk.Entry(win)
        recipient.pack(fill="x", padx=15)
        ttk.Label(win, text="Тема").pack(anchor="w", padx=15, pady=(12, 3))
        subject = ttk.Entry(win)
        subject.pack(fill="x", padx=15)
        text = tk.Text(win, wrap="word", font=("Segoe UI", 11))
        text.pack(fill="both", expand=True, padx=15, pady=15)
        if letter:
            recipient.insert(0, letter.reply_to)
            subject.insert(0, letter.subject if letter.subject.lower().startswith("re:") else "Re: " + letter.subject)
        def send():
            if self.busy:
                return
            to, title, body = recipient.get(), subject.get(), text.get("1.0", "end-1c")
            from .mail import make_message
            try:
                make_message(account, to, title, body)
            except ValueError as error:
                messagebox.showerror("Письмо", str(error), parent=win)
                return
            def done(_):
                win.destroy()
                self.status.set("Письмо передано SMTP-серверу")
            def operation():
                return send_message(account, to, title, body, letter.message_id if letter else "")
            self.work(operation, done)
        button = ttk.Button(win, text="Отправить", command=send)
        button.pack(anchor="e", padx=15, pady=(0, 15))


def main():
    App().mainloop()
