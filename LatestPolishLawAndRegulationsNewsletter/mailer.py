import smtplib
from email.message import EmailMessage
import json
from config import EMAIL_SENDER, EMAIL_PASSWORD

def send_summaries(summaries):
    with open("subscribers.json") as f:
        subscribers = json.load(f)

    for subscriber in subscribers:
        msg = EmailMessage()
        msg["Subject"] = "Podsumowanie nowych ustaw"
        msg["From"] = EMAIL_SENDER
        msg["To"] = subscriber["email"]

        body = "Dzień dobry,\n\nOto dzisiejsze podsumowanie ustaw:\n\n"
        for s in summaries:
            body += f"{s['title']}\n{s['summary']}\n{s['url']}\n\n"
        msg.set_content(body)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)

        print(f"Email wysłany do {subscriber['email']}")
