import openai
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import time
import threading

# ---------- Config ----------
API_KEY = "apikey"
QUESTION_COUNT = 5
TIME_LIMIT = 15  # seconds
PAUSE_BETWEEN_QUESTIONS = 1500  # milliseconds

# ---------- Database ----------
conn = sqlite3.connect("quiz_results.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nickname TEXT,
    category TEXT,
    score INTEGER,
    total INTEGER,
    duration REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# ---------- Quiz Generator ----------
class QuizGenerator:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)

    def fetch_questions(self, category: str, count: int = QUESTION_COUNT) -> list:
        prompt = (
            f"Wygeneruj {count} pyta\u0144 quizowych z kategorii '{category}'. "
            f"Ka\u017cde pytanie powinno mie\u0107 4 odpowiedzi (A, B, C, D) oraz wskazanie poprawnej odpowiedzi. "
            f"Zwr\u00f3\u0107 wynik w formacie:\n"
            f"Pytanie: <tre\u015b\u0107 pytania>\nA) <odpowied\u017a A>\nB) <odpowied\u017a B>\nC) <odpowied\u017a C>\nD) <odpowied\u017a D>\nOdpowied\u017a: <litera>\n"
        )

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Jeste\u015b generatorem pyta\u0144 quizowych."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )

        return self.parse_questions(response.choices[0].message.content.strip())

    def parse_questions(self, raw_text: str) -> list:
        questions = []
        blocks = raw_text.split("\n\n")
        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 6:
                continue
            question_text = lines[0].replace("Pytanie: ", "")
            options = {line[0]: line[3:] for line in lines[1:5]}
            correct = lines[5].replace("Odpowied\u017a: ", "").strip().upper()
            questions.append({"question": question_text, "options": options, "correct": correct})
        return questions

# ---------- GUI App ----------
class QuizApp:
    def __init__(self, root, generator):
        self.root = root
        self.generator = generator
        self.root.title("GPT Quiz Game")
        self.root.geometry("700x500")

        self.categories = [
            "Historia Polski", "Geografia Polski", "Historia \u015awiata", "Biologia", "Matematyka", "Fizyka", "Chemia", "Sztuka",
            "Film", "Muzyka", "Sport", "Informatyka", "Technologia", "Ekonomia", "Psychologia", "Astronomia",
            "Literatura", "J\u0119zyk polski", "J\u0119zyk angielski", "Religia"
        ]

        self.nickname = ""
        self.category = ""
        self.questions = []
        self.current_question_index = 0
        self.correct_answers = 0
        self.start_time = 0
        self.time_left = TIME_LIMIT
        self.timer_running = False

        self.build_start_screen()

    def build_start_screen(self):
        for w in self.root.winfo_children():
            w.destroy()

        tk.Label(self.root, text="Enter your nickname:", font=("Arial", 12)).pack(pady=5)
        self.nick_entry = tk.Entry(self.root, font=("Arial", 12))
        self.nick_entry.pack(pady=5)

        tk.Label(self.root, text="Choose quiz category:", font=("Arial", 12)).pack(pady=10)
        self.category_var = tk.StringVar()
        cb = ttk.Combobox(self.root, textvariable=self.category_var, values=self.categories, font=("Arial", 12))
        cb.pack()
        cb.current(0)

        tk.Button(self.root, text="Start Quiz", font=("Arial", 12), command=self.start_quiz).pack(pady=20)

    def start_quiz(self):
        self.nickname = self.nick_entry.get().strip()
        self.category = self.category_var.get()
        if not self.nickname:
            messagebox.showwarning("Warning", "Enter a nickname to continue!")
            return

        for w in self.root.winfo_children():
            w.destroy()

        tk.Label(self.root, text="Czekam na pytania...", font=("Arial", 14)).pack(pady=100)
        self.root.update()

        try:
            self.questions = self.generator.fetch_questions(self.category)
        except Exception as e:
            messagebox.showerror("Error", f"Problem z pobraniem pytan:\n{e}")
            self.build_start_screen()
            return

        self.correct_answers = 0
        self.current_question_index = 0
        self.start_time = time.time()
        self.show_question()

    def show_question(self):
        for w in self.root.winfo_children():
            w.destroy()

        if self.current_question_index >= len(self.questions):
            self.finish_quiz()
            return

        self.time_left = TIME_LIMIT
        self.timer_running = True

        q = self.questions[self.current_question_index]
        self.score_label = tk.Label(self.root, text=f"Wynik: {self.correct_answers}/{len(self.questions)}", anchor='e')
        self.score_label.place(x=520, y=10)

        tk.Label(self.root, text=f"Pytanie {self.current_question_index + 1}:", font=("Arial", 14)).pack(pady=10)
        tk.Label(self.root, text=q["question"], wraplength=600, font=("Arial", 12)).pack(pady=5)

        for k in ['A', 'B', 'C', 'D']:
            btn = tk.Button(self.root, text=f"{k}) {q['options'][k]}", font=("Arial", 12),
                            command=lambda c=k: self.check_answer(c))
            btn.pack(pady=4, fill="x", padx=80)

        self.progress = ttk.Progressbar(self.root, maximum=TIME_LIMIT, length=400, mode='determinate')
        self.progress.pack(pady=15)
        self.progress["value"] = TIME_LIMIT
        self.update_timer()

    def update_timer(self):
        if self.time_left > 0 and self.timer_running:
            self.time_left -= 1
            self.progress["value"] = self.time_left
            self.root.after(1000, self.update_timer)
        elif self.timer_running:
            self.check_answer(None)

    def check_answer(self, selected):
        self.timer_running = False
        q = self.questions[self.current_question_index]
        correct = q["correct"]

        for w in self.root.winfo_children():
            w.destroy()

        is_correct = (selected == correct)
        if is_correct:
            self.correct_answers += 1

        feedback = "✅ Poprawnie!" if is_correct else f"❌ B\u0142\u0119dnie. Poprawna odpowied\u017a to: {correct}"
        tk.Label(self.root, text=feedback, font=("Arial", 14)).pack(pady=30)
        self.root.after(PAUSE_BETWEEN_QUESTIONS, self.next_question)

    def next_question(self):
        self.current_question_index += 1
        self.show_question()

    def finish_quiz(self):
        duration = round(time.time() - self.start_time, 2)
        cursor.execute("""
            INSERT INTO scores (nickname, category, score, total, duration)
            VALUES (?, ?, ?, ?, ?)
        """, (self.nickname, self.category, self.correct_answers, len(self.questions), duration))
        conn.commit()

        for w in self.root.winfo_children():
            w.destroy()

        tk.Label(self.root, text=f"Tw\u00f3j wynik: {self.correct_answers}/{len(self.questions)}", font=("Arial", 16)).pack(pady=10)
        tk.Label(self.root, text=f"Czas: {duration} sek.", font=("Arial", 12)).pack(pady=5)

        tk.Label(self.root, text=f"Top 10 wynik\u00f3w:", font=("Arial", 14, "bold")).pack(pady=10)

        rows = cursor.execute("""
            SELECT nickname, category, score, total, duration
            FROM scores
            ORDER BY score DESC, duration ASC
            LIMIT 10
        """).fetchall()

        for r in rows:
            nick, cat, score, total, dur = r
            tk.Label(self.root, text=f"{nick} ({cat}) - {score}/{total} - {dur}s", font=("Arial", 10)).pack()

        tk.Button(self.root, text="Zagraj ponownie", command=self.build_start_screen).pack(pady=10)
        tk.Button(self.root, text="Wyj\u015bcie", command=self.root.quit).pack()


# ---------- Run ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = QuizApp(root, QuizGenerator(API_KEY))
    root.mainloop()
