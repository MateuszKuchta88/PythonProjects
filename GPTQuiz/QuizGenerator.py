# ---------- Quiz Generator ----------
from openai import OpenAI
import globals

class QuizGenerator:
    def __init__(self, api_key: str, language: str = "EN"):
        self.client = OpenAI(api_key=api_key)
        self.language = language

    def fetch_questions(self, category: str, count: int = globals.QUESTION_COUNT) -> list:
        # Dostosuj prompt do języka
        if self.language == "PL":
            prompt = (
                f"Wygeneruj {count} pytań quizowych z kategorii '{category}'. "
                f"Każde pytanie powinno mieć 4 odpowiedzi (A, B, C, D), poprawną odpowiedź i opcjonalnie obrazek."
                f" Format:\n"
                f"Pytanie: ...\nA) ...\nB) ...\nC) ...\nD) ...\nOdpowiedź: <litera>\nObrazek: <URL> (opcjonalnie)"
            )
        else:
            prompt = (
                f"Generate {count} quiz questions for category '{category}'. "
                f"Each question should have 4 answers (A, B, C, D), the correct answer and optionally an image."
                f" Format:\n"
                f"Question: ...\nA) ...\nB) ...\nC) ...\nD) ...\nAnswer: <letter>\nImage: <URL> (optional)"
            )
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a quiz question generator." if self.language != "PL" else "Jesteś generatorem pytań quizowych."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        raw = response.choices[0].message.content.strip()
        return self.parse_questions(raw)

    def parse_questions(self, raw_text: str) -> list:
        questions = []
        blocks = raw_text.split("\n\n")
        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 6:
                continue
            if self.language == "PL":
                # PL format
                q = lines[0].replace("Pytanie: ", "")
                options = {}
                for line in lines[1:5]:
                    if len(line) >= 3 and line[1] == ')':
                        options[line[0]] = line[3:].strip()

                correct = lines[5].replace("Odpowiedź: ", "").strip().upper()
                image = next((line.replace("Obrazek: ", "").strip() for line in lines if line.startswith("Obrazek:")), None)
            else:
                # EN format
                q = lines[0].replace("Question: ", "")
                options = {}
                for line in lines[1:5]:
                    if len(line) >= 3 and line[1] == ')':
                        options[line[0]] = line[3:].strip()

                correct = lines[5].replace("Answer: ", "").strip().upper()
                image = next((line.replace("Image: ", "").strip() for line in lines if line.startswith("Image:")), None)
            questions.append({"question": q, "options": options, "correct": correct, "image": image})
        return questions
