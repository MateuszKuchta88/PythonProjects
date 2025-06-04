import schedule
import time
from scraper import get_new_laws
from summarizer import summarize_laws
from mailer import send_summaries

def job():
    laws = get_new_laws()
    if laws:
        summaries = summarize_laws(laws)
        send_summaries(summaries)
    else:
        print("Brak nowych ustaw.")

def run_daily_task():
    schedule.every().day.at("10:00").do(job)
    print("Scheduler uruchomiony. Czekam na godzinę 10:00...")
    while True:
        schedule.run_pending()
        time.sleep(60)
