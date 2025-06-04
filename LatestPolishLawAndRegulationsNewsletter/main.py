# from scraper import get_new_laws
#
# laws = get_new_laws()
# if not laws:
#     print("Brak nowych ustaw.")
# else:
#     print(f"Pierwsza ustawa: {laws[0]['title']}")
#     print(laws[0]['content'][:2000])

import requests
from bs4 import BeautifulSoup
import os
import PyPDF2
import openai

# API key do OpenAI. Upewnij się, że jest poprawnie ustawiony.
openai_api_key = 'key'
openai.api_key = openai_api_key

# URL strony głównej.
url = "https://dziennikustaw.gov.pl/DU"

def find_latest_pdf_link(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Nie udało się nawiązać połączenia ze stroną.")

    soup = BeautifulSoup(response.content, 'html.parser')
    links = soup.find_all('a', href=True)
    pdf_links = [link['href'] for link in links if link['href'].endswith('.pdf')]
    return pdf_links[0] if pdf_links else None

def download_pdf(pdf_url, save_path):
    response = requests.get(pdf_url)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"Pobrano i zapisano plik jako: {save_path}")
    else:
        raise Exception("Nie udało się pobrać pliku PDF.")

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
    return text

def get_summary_from_openai(text):
    client = openai.OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Streszczaj nowe ustawy w prostym, zrozumiałym języku."},
            {"role": "user", "content": text}
        ],
        max_tokens=300
    )
    summary = response.choices[0].message.content.strip()
    return summary

try:
    latest_pdf_link = find_latest_pdf_link(url)
    if latest_pdf_link:
        pdf_url = requests.compat.urljoin(url, latest_pdf_link)
        save_path = os.path.join(os.getcwd(), 'najnowsza_ustawa.pdf')
        download_pdf(pdf_url, save_path)
        pdf_text = extract_text_from_pdf(save_path)
        summary = get_summary_from_openai(pdf_text)
        print("Streszczenie:", summary)
    else:
        print("Nie znaleziono żadnego linku do pliku PDF.")
except Exception as e:
    print(f"Wystąpił błąd: {e}")
