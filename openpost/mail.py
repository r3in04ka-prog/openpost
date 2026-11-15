"""Mail transport. No credentials or messages are written to disk."""
from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from email.message import EmailMessage
from email.utils import formatdate, make_msgid, getaddresses
import imaplib
import smtplib
import ssl


@dataclass(frozen=True)
class Account:
    address: str
    password: str
    imap_host: str
    smtp_host: str
    smtp_port: int = 465

    def validate(self):
        if not all((self.address.strip(), self.password, self.imap_host.strip(), self.smtp_host.strip())):
            raise ValueError("Заполните адрес, пароль и оба сервера.")
        if self.smtp_port not in (465, 587):
            raise ValueError("Используйте SMTP 465 (TLS) или 587 (STARTTLS).")


@dataclass(frozen=True)
class Letter:
    uid: str
    sender: str
    subject: str
    date: str
    body: str
    reply_to: str = ""
    message_id: str = ""


def parse_letter(uid, raw):
    msg = BytesParser(policy=policy.default).parsebytes(raw)
    part = msg.get_body(preferencelist=("plain",))
    body = "У письма нет текстовой версии. HTML и вложения пока не поддерживаются."
    if part is not None:
        try:
            body = part.get_content()
        except (LookupError, UnicodeError):
            body = part.get_payload(decode=True).decode("utf-8", errors="replace")
    return Letter(uid, str(msg.get("From", "")), str(msg.get("Subject", "Без темы")),
                  str(msg.get("Date", "")), body, str(msg.get("Reply-To", msg.get("From", ""))),
                  str(msg.get("Message-ID", "")))


def fetch_inbox(account, limit=50):
    account.validate()
    with imaplib.IMAP4_SSL(account.imap_host, 993, ssl_context=ssl.create_default_context(), timeout=20) as client:
        client.login(account.address, account.password)
        status, _ = client.select("INBOX", readonly=True)
        if status != "OK":
            raise RuntimeError("Не удалось открыть входящие.")
        status, data = client.uid("search", None, "ALL")
        if status != "OK":
            raise RuntimeError("Не удалось получить список писем.")
        letters = []
        for uid in reversed(data[0].split()[-limit:]):
            status, parts = client.uid("fetch", uid, "(BODY.PEEK[])")
            if status != "OK":
                raise RuntimeError("Не удалось загрузить письмо.")
            raw = next((item[1] for item in parts if isinstance(item, tuple)), None)
            if raw is not None:
                letters.append(parse_letter(uid.decode(), raw))
        return letters


def make_message(account, recipient, subject, body, reply_id=""):
    if "\r" in recipient or "\n" in recipient:
        raise ValueError("Некорректный получатель.")
    addresses = getaddresses([recipient])
    if not addresses or any("@" not in addr or not addr.rsplit("@", 1)[1] for _, addr in addresses):
        raise ValueError("Введите адрес получателя.")
    msg = EmailMessage()
    msg["From"] = account.address
    msg["To"] = recipient
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    if reply_id:
        msg["In-Reply-To"] = reply_id
        msg["References"] = reply_id
    msg.set_content(body)
    return msg


def send_message(account, recipient, subject, body, reply_id=""):
    account.validate()
    msg = make_message(account, recipient, subject, body, reply_id)
    context = ssl.create_default_context()
    if account.smtp_port == 465:
        transport = smtplib.SMTP_SSL(account.smtp_host, 465, context=context, timeout=20)
    else:
        transport = smtplib.SMTP(account.smtp_host, 587, timeout=20)
    with transport as client:
        if account.smtp_port == 587:
            client.ehlo()
            client.starttls(context=context)
            client.ehlo()
        client.login(account.address, account.password)
        refused = client.send_message(msg)
        if refused:
            raise RuntimeError("Сервер отклонил часть получателей. Не повторяйте отправку всем адресатам.")
