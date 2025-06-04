from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime
import fitz
import requests
import time

BASE_URL = "https://dziennikustaw.gov.pl/DU/rok/2025"

def get_new_laws():
    print("Uruchamiam przeglądarkę...")

    options = Options()
    options.add_argument("--headless")  # tryb bez GUI
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.get(BASE_URL)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.card-body"))
        )
    except Exception as e:
        print("⛔ Nie udało się znaleźć kart ustaw:", e)
        driver.quit()
        return []

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")

    today = datetime.now().date()
    new_laws = []

    for card in soup.select("div.card-body"):
        title_el = card.select_one("h5.card-title")
        subtitle_el = card.select_one("p.card-subtitle")
        pdf_link = card.select_one("a.btn[href*='DziennikUstaw.pdf']")

        if not (title_el and subtitle_el and pdf_link):
            continue

        title = title_el.get_text(strip=True)
        date_str = subtitle_el.get_text(strip=True).split(",")[-1].strip()
        try:
            pub_date = datetime.strptime(date_str, "%d.%m.%Y").date()
        except ValueError:
            continue

        if pub_date != today:
            continue

        pdf_url = "https://dziennikustaw.gov.pl" + pdf_link["href"]

        try:
            print(f"Pobieram PDF: {pdf_url}")
            response = requests.get(pdf_url)
            response.raise_for_status()
            text = extract_text_from_pdf(response.content)
            new_laws.append({
                "title": title,
                "url": pdf_url,
                "content": text
            })
        except Exception as e:
            print(f"Błąd przy pobieraniu PDF dla {title}: {e}")

    print(f"Znaleziono {len(new_laws)} nowych ustaw.")
    return new_laws

def extract_text_from_pdf(pdf_bytes):
    text = ""
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text.strip()
