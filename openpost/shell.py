"""OpenPost desktop shell: charcoal, rose accents and a paper-like reader."""
from pathlib import Path
import queue
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image
from .app import App as MailActions
from .mail import Account, Letter, fetch_inbox, make_message, send_message

BG = "#1c1e20"
SIDE = "#222426"
PANEL = "#252729"
ROSE = "#edb4c2"
MUTED = "#a5a0a2"
PAPER = "#f7f4f2"

ctk.set_appearance_mode("dark")


class App(ctk.CTk):
    work = MailActions.work
    poll = MailActions.poll
    refresh = MailActions.refresh

    def __init__(self):
        super().__init__()
        self.title("OpenPost")
        self.geometry("1180x740")
        self.minsize(960, 620)
        self.configure(fg_color=BG)
        self.account = None
        self.letters = []
        self.events = queue.Queue()
        self.busy = False
        self.current = None
        self.starred = set()
        self.filter = "Все"
        self.icons = {name: ctk.CTkImage(Image.open(Path(__file__).parent / "assets" / f"{name}.png"), size=(18, 18))
                      for name in ("Inbox", "Star", "Send", "Archive", "Trash2", "Plus", "Search", "RefreshCw", "UserRound", "Mail")}
        self.search = tk.StringVar()
        self.status = tk.StringVar(value="Подключите почту или откройте демо")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.sidebar = ctk.CTkFrame(self, width=205, corner_radius=0, fg_color=SIDE)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 1))
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(13, weight=1)
        ctk.CTkLabel(self.sidebar, text="openpost", font=("Segoe UI", 22, "bold"), anchor="w").grid(row=0, column=0, sticky="ew", padx=22, pady=(23, 22))
        ctk.CTkButton(self.sidebar, text="Новое письмо", image=self.icons["Plus"], height=43, corner_radius=22,
            fg_color=ROSE, hover_color="#dba1b0", text_color="#382d32", font=("Segoe UI", 13, "bold"), command=self.compose).grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 20))
        self.nav = {}
        for row, name in enumerate(["Входящие", "Важные", "Отправленные", "Архив", "Удалённые"], 2):
            enabled = name in ("Входящие", "Важные")
            icon_name = {"Входящие": "Inbox", "Важные": "Star", "Отправленные": "Send", "Архив": "Archive", "Удалённые": "Trash2"}[name]
            button = ctk.CTkButton(self.sidebar, text=name, image=self.icons[icon_name], anchor="w", height=37, corner_radius=9,
                fg_color="#393638" if name == "Входящие" else "transparent", hover_color="#343335",
                text_color="#e9e2e4" if enabled else "#716e71", font=("Segoe UI", 13),
                command=lambda n=name: self.navigate(n))
            button.grid(row=row, column=0, sticky="ew", padx=12, pady=2)
            self.nav[name] = button
        ctk.CTkLabel(self.sidebar, text="ПОЧТА", text_color=MUTED, font=("Segoe UI", 10, "bold"), anchor="w").grid(row=8, column=0, sticky="ew", padx=23, pady=(27, 10))
        self.account_name = ctk.CTkLabel(self.sidebar, text="Нет подключённых ящиков", text_color="#d7d0d2", font=("Segoe UI", 11), wraplength=165, anchor="w", justify="left")
        self.account_name.grid(row=9, column=0, sticky="ew", padx=23, pady=8)
        ctk.CTkButton(self.sidebar, text="Подключить почту", fg_color="transparent", border_width=1, border_color="#504248", text_color=ROSE, hover_color="#343034", height=34, command=self.connect).grid(row=10, column=0, sticky="ew", padx=17, pady=8)
        ctk.CTkButton(self.sidebar, text="Деморежим", fg_color="transparent", text_color=MUTED, hover_color="#343034", command=self.demo).grid(row=14, column=0, sticky="ew", padx=17, pady=(8, 15))
        main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)
        toolbar = ctk.CTkFrame(main, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=16, pady=(19, 12))
        toolbar.grid_columnconfigure(0, weight=1)
        self.search_entry = ctk.CTkEntry(toolbar, placeholder_text="Поиск в личных и рабочих письмах…",
            height=40, corner_radius=20, fg_color="#2c2e30", border_width=0, text_color="#eee7e9")
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 14))
        self.search_entry.bind("<KeyRelease>", lambda _: self.search.set(self.search_entry.get()))
        ctk.CTkButton(toolbar, text="", image=self.icons["RefreshCw"], width=35, height=35, fg_color="transparent", text_color=MUTED, hover_color=PANEL, command=self.refresh).grid(row=0, column=1)
        tabs = ctk.CTkFrame(main, fg_color="transparent")
        tabs.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 13))
        self.tab_buttons = {}
        for i, name in enumerate(["Все", "Важные", "Люди", "Рассылки"]):
            btn = ctk.CTkButton(tabs, text=name, width=65 if i == 0 else 85, height=30, corner_radius=10,
                fg_color="#efd9cf" if i == 0 else "transparent", text_color="#4a3936" if i == 0 else "#d2cdd0",
                hover_color="#73535f", font=("Segoe UI", 12, "bold"), command=lambda n=name: self.set_filter(n))
            btn.pack(side="left", padx=(0, 5))
            self.tab_buttons[name] = btn
        content = ctk.CTkFrame(main, fg_color="transparent")
        content.grid(row=2, column=0, sticky="nsew", padx=(8, 14), pady=(0, 8))
        content.grid_columnconfigure(0, weight=4, minsize=270)
        content.grid_columnconfigure(1, weight=5, minsize=340)
        content.grid_rowconfigure(0, weight=1)
        self.message_list = ctk.CTkScrollableFrame(content, fg_color=BG, corner_radius=0, scrollbar_button_color="#414043", scrollbar_button_hover_color="#65515a")
        self.message_list.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        self.message_list.grid_columnconfigure(0, weight=1)
        self.reader = ctk.CTkFrame(content, fg_color=PAPER, corner_radius=13)
        self.reader.grid(row=0, column=1, sticky="nsew")
        self.reader.grid_columnconfigure(0, weight=1)
        self.reader.grid_rowconfigure(3, weight=1)
        self.title_label = ctk.CTkLabel(self.reader, text="Ваша почта. Ваше пространство.", anchor="w", text_color="#2f2b2c", font=("Segoe UI", 17, "bold"), wraplength=390, justify="left")
        self.title_label.grid(row=0, column=0, sticky="ew", padx=22, pady=(16, 8))
        self.sender_label = ctk.CTkLabel(self.reader, text="", text_color="#6d6568", font=("Segoe UI", 12), justify="left", anchor="w", wraplength=380)
        self.sender_label.grid(row=1, column=0, sticky="ew", padx=22, pady=(0, 15))
        self.content_frame = ctk.CTkScrollableFrame(self.reader, fg_color=PAPER, corner_radius=0, scrollbar_button_color="#d9d1d2", scrollbar_button_hover_color="#b7a2aa")
        self.content_frame.grid(row=3, column=0, sticky="nsew", padx=12)
        self.content_frame.grid_columnconfigure(0, weight=1)
        footer = ctk.CTkFrame(self.reader, fg_color="#ebe5e5", corner_radius=18)
        footer.grid(row=4, column=0, sticky="ew", padx=16, pady=16)
        ctk.CTkButton(footer, text="Ответить…", anchor="w", fg_color="transparent", text_color="#887d82", hover_color="#e3dadc", height=38, command=self.reply).pack(side="left", fill="x", expand=True, padx=4)
        self.star_button = ctk.CTkButton(footer, text="В важные", width=84, fg_color="transparent", text_color="#887d82", hover_color="#e3dadc", command=self.toggle_star)
        self.star_button.pack(side="right", padx=4)
        ctk.CTkLabel(main, textvariable=self.status, text_color="#8f888d", font=("Segoe UI", 10), anchor="w").grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 10))
        self.search.trace_add("write", lambda *_: self.render())
        self.show_body("Подключите почтовый ящик или нажмите «Деморежим», чтобы посмотреть, как всё устроено.")
        self.after(100, self.poll)

    def navigate(self, name):
        if name not in ("Входящие", "Важные"):
            messagebox.showinfo("OpenPost", "Эта папка пока не поддерживается. Сейчас доступны входящие и локальные важные письма.", parent=self)
            return
        for n, button in self.nav.items():
            button.configure(fg_color="#393638" if n == name else "transparent")
        self.set_filter("Важные" if name == "Важные" else "Все")

    def set_filter(self, name):
        self.filter = name
        for n, button in self.tab_buttons.items():
            button.configure(fg_color="#efd9cf" if n == name else "transparent", text_color="#4a3936" if n == name else "#d2cdd0")
        self.render()

    def loaded(self, letters):
        self.letters = letters
        self.current = None
        self.starred.clear()
        self.render()
        self.status.set(f"Входящие · {len(letters)} писем · Последние 50")
        if self.account:
            self.account_name.configure(text=self.account.address)

    def render(self):
        for widget in self.message_list.winfo_children():
            widget.destroy()
        query = self.search.get().casefold()
        visible = []
        for i, letter in enumerate(self.letters):
            newsletter = any(word in letter.sender.casefold() for word in ("noreply", "newsletter", "pinterest", "news@"))
            if query not in f"{letter.sender} {letter.subject} {letter.body}".casefold():
                continue
            if self.filter == "Важные" and letter.uid not in self.starred:
                continue
            if self.filter == "Люди" and newsletter or self.filter == "Рассылки" and not newsletter:
                continue
            visible.append(i)
        if self.current not in visible:
            self.current = visible[0] if visible else None
        for row, i in enumerate(visible):
            letter = self.letters[i]
            selected = i == self.current
            card = ctk.CTkFrame(self.message_list, fg_color="#634b55" if selected else "transparent", corner_radius=10, cursor="hand2")
            card.grid(row=row, column=0, sticky="ew", pady=2)
            card.grid_columnconfigure(1, weight=1)
            avatar = ctk.CTkFrame(card, width=32, height=32, corner_radius=16, fg_color="#b18f9c" if selected else "#51454c")
            avatar.grid(row=0, column=0, rowspan=3, padx=(10, 8), sticky="n", pady=12)
            avatar.grid_propagate(False)
            avatar_label = ctk.CTkLabel(avatar, text="", image=self.icons["UserRound"], width=32, height=32)
            avatar_label.pack()
            sender = letter.sender.split("<")[0].strip() or letter.sender
            sender = sender[:21] + ("…" if len(sender) > 21 else "")
            title = ctk.CTkLabel(card, text=sender, height=20, font=("Segoe UI", 13, "bold"), text_color="#eee7e9", anchor="w")
            title.grid(row=0, column=1, sticky="ew", padx=(0, 5), pady=(8, 0))
            time = letter.date if letter.uid.startswith("demo") else ""
            ctk.CTkLabel(card, text=time, height=20, font=("Segoe UI", 10), text_color="#c0b7bc").grid(row=0, column=2, padx=(0, 10), pady=(8, 0))
            subject = ctk.CTkLabel(card, text=letter.subject[:29], height=20, text_color="#e4dce0", font=("Segoe UI", 12), anchor="w")
            subject.grid(row=1, column=1, columnspan=2, sticky="ew", padx=(0, 10))
            preview = ctk.CTkLabel(card, text=letter.body.replace("\n", " ")[:31] + "…", height=18, text_color="#ada4aa", font=("Segoe UI", 11), anchor="w")
            preview.grid(row=2, column=1, columnspan=2, sticky="ew", padx=(0, 10), pady=(0, 8))
            for widget in (card, title, subject, preview, avatar, avatar_label):
                widget.bind("<Button-1>", lambda _, index=i: self.select(index))
        if not visible:
            ctk.CTkLabel(self.message_list, text="Здесь пока нет писем", text_color=MUTED).grid(row=0, column=0, pady=35)
        self.read()

    def select(self, index):
        self.current = index
        self.render()

    def selected(self):
        return self.letters[self.current] if self.current is not None else None

    def show_body(self, text):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        body = ctk.CTkTextbox(self.content_frame, fg_color=PAPER, text_color="#51494c", font=("Segoe UI", 14), wrap="word", height=125 if self.selected() and self.selected().uid == "demo-clinic" else 250, border_width=0, activate_scrollbars=True)
        body.grid(row=0, column=0, sticky="ew", padx=4)
        body.insert("1.0", text)
        body.configure(state="disabled")

    def read(self, *_):
        letter = self.selected()
        if not letter:
            self.title_label.configure(text="Ваша почта. Ваше пространство.")
            self.sender_label.configure(text="")
            self.show_body("Выберите письмо из списка слева.")
            return
        self.title_label.configure(text=letter.subject)
        self.sender_label.configure(text=f"{letter.sender}\nкому: мне  ·  {letter.date}")
        self.star_button.configure(text="Убрать" if letter.uid in self.starred else "В важные")
        self.show_body(letter.body)
        photo = Path(__file__).parent / "assets" / "clinic.png"
        if letter.uid == "demo-clinic" and photo.exists():
            from PIL import ImageOps
            self.photo = ctk.CTkImage(ImageOps.fit(Image.open(photo), (680, 300)), size=(340, 150))
            ctk.CTkLabel(self.content_frame, text="", image=self.photo, corner_radius=10).grid(row=1, column=0, pady=(8, 0))

    def toggle_star(self):
        letter = self.selected()
        if letter:
            if letter.uid in self.starred:
                self.starred.remove(letter.uid)
            else:
                self.starred.add(letter.uid)
            self.render()

    def demo(self):
        if self.busy:
            return
        self.account = None
        self.account_name.configure(text="Демонстрационный ящик")
        self.search.set("")
        self.search_entry.delete(0, "end")
        self.filter = "Все"
        self.loaded([
            Letter("demo-clinic", "Smile Talk Clinic", "Подтверждение записи", "12:24", "Здравствуйте, Анастасия!\n\nПодтверждаем вашу запись на профессиональную гигиену зубов 17 октября в 16:00.\n\nЖдём вас в Smile Talk!", "hello@example.org"),
            Letter("demo-client", "Клиенты", "Новый запрос с сайта", "11:41", "Здравствуйте! Хотела уточнить стоимость и свободные даты на следующей неделе.", "client@example.org"),
            Letter("demo-supply", "Поставщики", "Счёт на оплату", "10:18", "Во вложении счёт и договор. Пожалуйста, подтвердите получение.", "supply@example.org"),
            Letter("demo-team", "Команда", "План на неделю", "Вчера", "Привет! Отправляю план на эту неделю. Давайте обсудим его на встрече.", "team@example.org"),
            Letter("demo-personal", "Личное", "Бронирование отеля", "Вчера", "Подтверждение бронирования номера. Будем рады видеть вас!", "hotel@example.org"),
            Letter("demo-news", "Pinterest <news@example.org>", "Новые идеи", "Вчера", "Мы подобрали для вас новые идеи для дома и работы.", "news@example.org")])
        self.status.set("Деморежим · Пример писем · Отправка отключена")

    def dialog(self, title, labels):
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.geometry("470x530")
        win.configure(fg_color=SIDE)
        win.transient(self)
        win.after(100, win.grab_set)
        ctk.CTkLabel(win, text=title, font=("Segoe UI", 22, "bold")).pack(anchor="w", padx=26, pady=(22, 18))
        fields = []
        for label, default, secret in labels:
            ctk.CTkLabel(win, text=label, text_color=MUTED, anchor="w").pack(fill="x", padx=26)
            entry = ctk.CTkEntry(win, height=36, fg_color="#2e3033", border_color="#494047", show="•" if secret else "")
            entry.insert(0, default)
            entry.pack(fill="x", padx=26, pady=(3, 10))
            fields.append(entry)
        return win, fields

    def connect(self):
        if self.busy:
            return
        win, fields = self.dialog("Подключить почту", [("Email", "", False), ("Пароль приложения", "", True), ("IMAP сервер · TLS 993", "", False), ("SMTP сервер", "", False), ("SMTP порт · TLS 465 / STARTTLS 587", "465", False)])
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
        ctk.CTkButton(win, text="Подключить", fg_color=ROSE, text_color="#382d32", hover_color="#dba1b0", height=38, command=save).pack(fill="x", padx=26, pady=10)

    def reply(self):
        letter = self.selected()
        if letter:
            self.compose(letter)

    def compose(self, letter=None):
        if not self.account:
            messagebox.showinfo("OpenPost", "Для отправки подключите почту. В деморежиме отправка отключена.", parent=self)
            return
        account = self.account
        win, fields = self.dialog("Новое письмо", [("Кому", letter.reply_to if letter else "", False), ("Тема", (letter.subject if letter.subject.lower().startswith("re:") else "Re: " + letter.subject) if letter else "", False)])
        body = ctk.CTkTextbox(win, fg_color="#2e3033", font=("Segoe UI", 13), wrap="word")
        body.pack(fill="both", expand=True, padx=26, pady=10)
        def send():
            if self.busy:
                return
            to, title, text = fields[0].get(), fields[1].get(), body.get("1.0", "end-1c")
            try:
                make_message(account, to, title, text)
            except ValueError as error:
                messagebox.showerror("Письмо", str(error), parent=win)
                return
            def done(_):
                if win.winfo_exists():
                    win.destroy()
                self.status.set("Письмо передано SMTP-серверу")
            self.work(lambda: send_message(account, to, title, text, letter.message_id if letter else ""), done)
        ctk.CTkButton(win, text="Отправить письмо", fg_color=ROSE, text_color="#382d32", hover_color="#dba1b0", height=38, command=send).pack(fill="x", padx=26, pady=(5, 22))


def main():
    App().mainloop()
