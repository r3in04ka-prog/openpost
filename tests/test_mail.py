import unittest
from unittest.mock import patch, MagicMock
from openpost.mail import Account, parse_letter, make_message, fetch_inbox, send_message


class MailTests(unittest.TestCase):
    def setUp(self):
        self.account = Account("me@example.org", "test-only", "imap.example.org", "smtp.example.org")

    def test_mime_and_html_fallback(self):
        raw = "From: Alice <alice@example.org>\nSubject: Привет\nContent-Type: text/plain; charset=utf-8\n\nПисьмо".encode()
        letter = parse_letter("1", raw)
        self.assertEqual(letter.subject, "Привет")
        self.assertEqual(letter.body, "Письмо")
        html = parse_letter("2", b"Content-Type: text/html\n\n<script>bad()</script>")
        self.assertNotIn("<script>", html.body)

    def test_reply_and_recipient_validation(self):
        msg = make_message(self.account, "you@example.org", "Re: Hello", "Hi", "<original@example.org>")
        self.assertEqual(msg["In-Reply-To"], "<original@example.org>")
        self.assertIn("Hi", msg.get_content())
        for recipient in ("", "invalid", "a@example.org\nBcc: x@example.org"):
            with self.assertRaises(ValueError):
                make_message(self.account, recipient, "Hello", "Hi")

    @patch("openpost.mail.imaplib.IMAP4_SSL")
    def test_inbox_uses_readonly_and_peek(self, factory):
        client = factory.return_value.__enter__.return_value
        client.select.return_value = ("OK", [])
        client.uid.side_effect = [("OK", [b"1 2 3"]), ("OK", [(b"3", b"Subject: Three\n\nBody")]), ("OK", [(b"2", b"Subject: Two\n\nBody")])]
        letters = fetch_inbox(self.account, limit=2)
        self.assertEqual([x.uid for x in letters], ["3", "2"])
        client.select.assert_called_once_with("INBOX", readonly=True)
        self.assertEqual(client.uid.call_args.args, ("fetch", b"2", "(BODY.PEEK[])"))
        context = factory.call_args.kwargs["ssl_context"]
        self.assertTrue(context.check_hostname)

    @patch("openpost.mail.smtplib.SMTP")
    def test_starttls_before_login(self, factory):
        client = factory.return_value.__enter__.return_value
        client.send_message.return_value = {}
        account = Account("me@example.org", "test-only", "imap.example.org", "smtp.example.org", 587)
        send_message(account, "you@example.org", "Hello", "Hi")
        names = [call[0] for call in client.method_calls]
        self.assertLess(names.index("starttls"), names.index("login"))
        self.assertTrue(client.starttls.call_args.kwargs["context"].check_hostname)

    @patch("openpost.mail.smtplib.SMTP_SSL")
    def test_tls_and_partial_refusal(self, factory):
        client = factory.return_value.__enter__.return_value
        client.send_message.return_value = {"you@example.org": (550, b"refused")}
        with self.assertRaises(RuntimeError):
            send_message(self.account, "you@example.org", "Hello", "Hi")
        self.assertTrue(factory.call_args.kwargs["context"].check_hostname)


if __name__ == "__main__":
    unittest.main()
