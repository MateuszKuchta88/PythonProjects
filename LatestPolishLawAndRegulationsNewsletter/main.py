import requests
from bs4 import BeautifulSoup
import os
import PyPDF2
import openai
from fpdf import FPDF
import config
import re
import datetime


class LawSummaryGenerator:
    def __init__(self, base_url, openai_api_key, save_dir="pdfs", summary_pdf="streszczenia.pdf"):
        self.base_url = base_url
        self.api_key = openai_api_key
        self.save_dir = save_dir
        self.summary_pdf = summary_pdf
        os.makedirs(self.save_dir, exist_ok=True)

    def find_latest_pdf_links(self, count=config.COUNT_OF_FILES):
        response = requests.get(self.base_url)
        if response.status_code != 200:
            raise Exception("Nie udało się nawiązać połączenia ze stroną.")

        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all('a', href=True)
        pdf_links = [link['href'] for link in links if link['href'].endswith('.pdf')]
        return pdf_links[:count] if pdf_links else []

    @staticmethod
    def sanitize_filename(text):
        # Usuwamy niedozwolone znaki, zostawiamy litery/cyfry/spacje
        sanitized = re.sub(r'[^\w\s-]', '', text)
        sanitized = re.sub(r'\s+', '_', sanitized.strip())  # Zamieniamy spacje na _
        return sanitized

    def extract_title_from_text(self, text):
        lines = text.split('\n')
        for line in lines:
            if re.search(r"(ustawa|rozporządzenie).*z dnia", line, re.IGNORECASE):
                title = re.sub(r'\s+', ' ', line.strip())
                return title
        return "Nieznany_akt"

    def extract_title_from_pdf(self, filepath, fallback="ustawa"):
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            if reader.pages:
                text = reader.pages[0].extract_text()
                if text:
                    # Tytuł zazwyczaj w 1-3 linijce
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    if lines:
                        title_candidate = lines[0]
                        return self.sanitize_filename(title_candidate)
        return fallback

    def download_pdf(self, pdf_url):
        response = requests.get(pdf_url)
        if response.status_code == 200:
            temp_path = os.path.join(self.save_dir, "temp.pdf")
            with open(temp_path, 'wb') as f:
                f.write(response.content)

            # Wydobycie tekstu
            text = self.extract_text_from_pdf(temp_path)
            title = self.extract_title_from_text(text)

            # Czyszczenie tytułu dla pliku
            safe_title = re.sub(r'[\\/*?:"<>|]', "", title)[:100]  # ograniczenie długości + niedozwolone znaki
            date_str = datetime.datetime.now().strftime("%Y%m%d")
            final_filename = f"{safe_title} {date_str}.pdf"
            final_path = os.path.join(self.save_dir, final_filename)

            # Unikaj konfliktów nazw
            counter = 1
            while os.path.exists(final_path):
                final_filename = f"{safe_title} {date_str}_{counter}.pdf"
                final_path = os.path.join(self.save_dir, final_filename)
                counter += 1

            os.rename(temp_path, final_path)
            print(f"Pobrano: {final_filename}")
            return final_path, final_filename
        else:
            raise Exception(f"Nie udało się pobrać pliku PDF: {pdf_url}")

    @staticmethod
    def extract_text_from_pdf(filepath):
        with open(filepath, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ''.join(page.extract_text() or '' for page in reader.pages)
        return text

    def summarize_text(self, text, max_chars=4000):
        trimmed_text = text[:max_chars]  # ograniczamy długość
        client = openai.OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Streszczaj nowe ustawy w prostym, zrozumiałym języku. Zmieść się z odpowiedzią w 250 tokenach."},
                {"role": "user", "content": trimmed_text}
            ],
            max_tokens=400
        )
        return response.choices[0].message.content.strip()

    def write_summaries_to_pdf(self, summaries):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Dodaj czcionkę z pliku .ttf (raz, przed użyciem)
        font_path = "DejaVuSans.ttf"  # <-- upewnij się, że masz ten plik w folderze projektu
        pdf.add_font("DejaVu", "", font_path, uni=True)
        pdf.set_font("DejaVu", size=12)

        for idx, (filename, summary) in enumerate(summaries, 1):
            pdf.set_font("DejaVu", size=12)
            pdf.cell(0, 10, f"Streszczenie {idx}: {filename}", ln=True)
            pdf.set_font("DejaVu", size=12)
            for line in summary.split('\n'):
                pdf.multi_cell(0, 10, line)
            pdf.ln()

        pdf.output(self.summary_pdf)
        print(f"Streszczenia zapisane do pliku: {self.summary_pdf}")

    def run(self):
        try:
            pdf_links = self.find_latest_pdf_links(count=config.COUNT_OF_FILES)
            if not pdf_links:
                print("Nie znaleziono żadnych plików PDF.")
                return

            summaries = []
            for idx, relative_url in enumerate(pdf_links):
                full_url = requests.compat.urljoin(self.base_url, relative_url)
                pdf_path, filename = self.download_pdf(full_url)
                text = self.extract_text_from_pdf(pdf_path)
                summary = self.summarize_text(text)
                summaries.append((filename, summary))

            self.write_summaries_to_pdf(summaries)

        except Exception as e:
            print(f"Wystąpił błąd: {e}")


if __name__ == "__main__":
    generator = LawSummaryGenerator(
        base_url="https://dziennikustaw.gov.pl/DU",
        openai_api_key="apikey"
    )
    generator.run()
