# ---------- Aplikacja GUI ----------
import tkinter as tk
import sqlite3
from tkinter import ttk, messagebox
import time
import threading
from PIL import Image, ImageTk
import requests
from io import BytesIO
from QuizGenerator import QuizGenerator
import platform
import globals

if platform.system() == "Windows":
    import winsound

# ---------- Baza danych ----------
conn = sqlite3.connect(globals.DB_NAME)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nickname TEXT,
    category TEXT,
    score INTEGER,
    total INTEGER,
    duration REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    language TEXT
)
""")
conn.commit()

class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GPT Quiz Game")
        self.root.geometry("800x600")
        self.nickname = ""
        self.category = ""
        self.questions = []
        self.current_question_index = 0
        self.correct_answers = 0
        self.start_time = 0
        self.time_left = globals.TIME_LIMIT
        self.timer_running = False
        self.generator = None
        self.language = "EN"  # default language
        self.mode_online = True  # domyślnie online (GPT)
        self.categories = {
            "PL": [
                "Historia Polski", "Geografia Polski", "Historia świata", "Biologia", "Matematyka",
                "Fizyka", "Chemia", "Sztuka", "Film", "Muzyka", "Sport", "Informatyka",
                "Technologia", "Ekonomia", "Psychologia", "Astronomia", "Literatura",
                "Język polski", "Język angielski", "Religia"
            ],
            "EN": [
                "Polish History", "Polish Geography", "World History", "Biology", "Math",
                "Physics", "Chemistry", "Art", "Film", "Music", "Sport", "Computer Science",
                "Technology", "Economics", "Psychology", "Astronomy", "Literature",
                "Polish Language", "English Language", "Religion"
            ]
        }
        self.translations = {
            "EN": {
                "api_key_prompt": "Enter your OpenAI API Key:",
                "next": "Next",
                "start_quiz": "Start Quiz",
                "nickname_prompt": "Enter your nickname:",
                "choose_category": "Choose category:",
                "warning_api": "Please enter API Key!",
                "warning_nick": "Please enter nickname!",
                "quiz_gen_msg": "Generating random questions for category '{}' via ChatGPT...",
                "correct": "✅ Correct!",
                "incorrect": "❌ Wrong. Correct answer: {}",
                "time_left": "Time left: {:.1f}s",
                "result": "Score: {}/{}",
                "time": "Time: {} sec.",
                "rank": "Your rank: {}",
                "top_scores": "Top 10 scores:",
                "play_again": "Play again",
                "exit": "Exit",
                "select_language": "Select quiz language:",
                "select_mode": "Select quiz mode:",
                "online": "Online (GPT)",
                "offline": "Offline (local questions)",
                "answer_prompt": "Answer:",
                "question_prompt": "Question {} / {}",
                "category_prompt": "Category:",
                "loading": "Loading...",
            },
            "PL": {
                "api_key_prompt": "Podaj swój OpenAI API Key:",
                "next": "Dalej",
                "start_quiz": "Rozpocznij Quiz",
                "nickname_prompt": "Podaj swój nick:",
                "choose_category": "Wybierz kategorię:",
                "warning_api": "Podaj klucz API!",
                "warning_nick": "Podaj nick!",
                "quiz_gen_msg": "Trwa generacja losowych pytań z kategorii '{}' przez ChatGPT...",
                "correct": "✅ Poprawnie!",
                "incorrect": "❌ Błędnie. Poprawna odpowiedź to: {}",
                "time_left": "Pozostało: {:.1f}s",
                "result": "Wynik: {}/{}",
                "time": "Czas: {} sek.",
                "rank": "Twoje miejsce w rankingu: {}",
                "top_scores": "Top 10 wyników:",
                "play_again": "Zagraj ponownie",
                "exit": "Wyjście",
                "select_language": "Wybierz język quizu:",
                "select_mode": "Wybierz tryb quizu:",
                "online": "Online (GPT)",
                "offline": "Offline (lokalne pytania)",
                "answer_prompt": "Odpowiedź:",
                "question_prompt": "Pytanie {} / {}",
                "category_prompt": "Kategoria:",
                "loading": "Ładowanie...",
            }
        }
        self.ask_language_mode_screen()

    def t(self, key):
        return self.translations[self.language].get(key, key)

    def ask_language_mode_screen(self):
        for w in self.root.winfo_children():
            w.destroy()
        tk.Label(self.root, text=self.t("select_language"), font=("Arial", 16)).pack(pady=20)
        self.lang_var = tk.StringVar(value="EN")
        lang_frame = tk.Frame(self.root)
        lang_frame.pack()
        tk.Radiobutton(lang_frame, text="English", variable=self.lang_var, value="EN", font=("Arial", 14)).pack(side="left", padx=10)
        tk.Radiobutton(lang_frame, text="Polski", variable=self.lang_var, value="PL", font=("Arial", 14)).pack(side="left", padx=10)

        tk.Label(self.root, text=self.t("select_mode"), font=("Arial", 16)).pack(pady=20)
        self.mode_var = tk.StringVar(value="online")
        mode_frame = tk.Frame(self.root)
        mode_frame.pack()
        tk.Radiobutton(mode_frame, text=self.t("online"), variable=self.mode_var, value="online", font=("Arial", 14)).pack(side="left", padx=10)
        tk.Radiobutton(mode_frame, text=self.t("offline"), variable=self.mode_var, value="offline", font=("Arial", 14)).pack(side="left", padx=10)

        tk.Button(self.root, text=self.t("next"), font=("Arial", 14), command=self.save_language_mode).pack(pady=30)

    def save_language_mode(self):
        self.language = self.lang_var.get()
        self.mode_online = (self.mode_var.get() == "online")
        self.build_start_screen()

    def build_start_screen(self):
        for w in self.root.winfo_children():
            w.destroy()
        if self.mode_online:
            tk.Label(self.root, text=self.t("api_key_prompt"), font=("Arial", 14)).pack(pady=20)
            self.api_entry = tk.Entry(self.root, font=("Arial", 14), show="*")
            self.api_entry.pack(pady=5)
            tk.Button(self.root, text=self.t("next"), font=("Arial", 12), command=self.save_api_key).pack(pady=10)
        else:
            self.build_nick_cat_screen()

    def save_api_key(self):
        key = self.api_entry.get().strip()
        if not key:
            messagebox.showwarning(self.t("warning_api"), self.t("warning_api"))
            return
        self.generator = QuizGenerator(key, language=self.language)
        self.build_nick_cat_screen()

    def build_nick_cat_screen(self):
        for w in self.root.winfo_children():
            w.destroy()
        tk.Label(self.root, text=self.t("nickname_prompt"), font=("Arial", 14)).pack(pady=10)
        self.nick_entry = tk.Entry(self.root, font=("Arial", 14))
        self.nick_entry.pack(pady=5)

        tk.Label(self.root, text=self.t("choose_category"), font=("Arial", 14)).pack(pady=10)
        self.category_var = tk.StringVar()
        cb = ttk.Combobox(self.root, textvariable=self.category_var, values=self.categories[self.language], font=("Arial", 12))
        cb.pack()
        cb.current(0)

        tk.Button(self.root, text=self.t("start_quiz"), font=("Arial", 14), bg="#007BFF", fg="white",
                  command=self.start_quiz).pack(pady=20)

    def start_quiz(self):
        self.nickname = self.nick_entry.get().strip()
        self.category = self.category_var.get()
        if not self.nickname:
            messagebox.showwarning(self.t("warning_nick"), self.t("warning_nick"))
            return
        for w in self.root.winfo_children():
            w.destroy()
        if self.mode_online:
            self.show_loading_message(self.t("quiz_gen_msg").format(self.category))
            threading.Thread(target=self.load_questions_online, daemon=True).start()
        else:
            self.questions = globals.LOCAL_QUESTIONS[self.language].get(self.category, [])
            if not self.questions:
                messagebox.showerror("Error", "No offline questions available for this category.")
                self.build_nick_cat_screen()
                return
            self.setup_quiz()

    def show_loading_message(self, message):
        self.loading_label = tk.Label(self.root, text=message, font=("Arial", 14))
        self.loading_label.pack(pady=40)

    def load_questions_online(self):
        try:
            self.questions = self.generator.fetch_questions(self.category)
            if not self.questions:
                raise Exception("No questions received from GPT")
            self.root.after(0, self.setup_quiz)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to get questions: {e}"))
            self.root.after(0, self.build_nick_cat_screen)

    def setup_quiz(self):
        for w in self.root.winfo_children():
            w.destroy()
        self.current_question_index = 0
        self.correct_answers = 0
        self.start_time = time.time()
        self.time_left = globals.TIME_LIMIT
        self.timer_running = False

        # UI: pytanie, kategoria, obrazek
        self.label_category = tk.Label(self.root, text=f"{self.t('category_prompt')} {self.category}", font=("Arial", 14))
        self.label_category.pack(pady=5)
        self.label_question_num = tk.Label(self.root, text="", font=("Arial", 16, "bold"))
        self.label_question_num.pack(pady=5)
        self.label_question = tk.Label(self.root, text="", font=("Arial", 14), wraplength=750, justify="left")
        self.label_question.pack(pady=10)

        self.image_label = tk.Label(self.root)
        self.image_label.pack()

        # Opcje odpowiedzi
        self.answer_var = tk.StringVar()
        self.buttons_frame = tk.Frame(self.root)
        self.buttons_frame.pack(pady=20, fill='x', expand=True)

        self.answer_buttons = {}
        for option in ["A", "B", "C", "D"]:
            btn = tk.Radiobutton(
                self.buttons_frame,
                text="",
                variable=self.answer_var,
                value=option,
                font=("Arial", 14),
                indicatoron=0,
                pady=10,
                command=self.answer_selected,
                wraplength=150,  # wrap text after 150 pixels if too long
                justify='center'
            )
            btn.pack(side="left", padx=10, fill='x', expand=True)
            self.answer_buttons[option] = btn

        # Pasek postępu czasu
        self.progress = ttk.Progressbar(self.root, orient='horizontal', length=600, mode='determinate')
        self.progress.pack(pady=10)

        # Label czasu
        self.time_label = tk.Label(self.root, text="", font=("Arial", 14))
        self.time_label.pack()

        self.feedback_label = tk.Label(self.root, text="", font=("Arial", 16, "bold"))
        self.feedback_label.pack(pady=10)

        self.next_button = tk.Button(self.root, text=self.t("next"), font=("Arial", 14), command=self.next_question, state="disabled")
        self.next_button.pack(pady=20)

        self.load_question(self.current_question_index)

    def load_question(self, index):
        self.feedback_label.config(text="", bg=self.root.cget("bg"))
        q = self.questions[index]
        self.label_question_num.config(text=self.t("question_prompt").format(index + 1, len(self.questions)))
        self.label_question.config(text=q["question"])
        self.answer_var.set(None)

        # Ustaw odpowiedzi
        for opt in ["A", "B", "C", "D"]:
            self.answer_buttons[opt].config(text=f"{opt}) {q['options'][opt]}", state="normal", bg=self.root.cget("bg"))

        # Wczytaj obrazek jeśli jest
        if q.get("image"):
            try:
                response = requests.get(q["image"], timeout=5)
                response.raise_for_status()
                img = Image.open(BytesIO(response.content))
                img.thumbnail((400, 300))
                self.imgtk = ImageTk.PhotoImage(img)
                self.image_label.config(image=self.imgtk, text="")
            except Exception as e:
                self.image_label.config(image="", text="❌ Failed to load image.")
        else:
            self.image_label.config(image="", text="")

        self.time_left = globals.TIME_LIMIT
        self.progress["maximum"] = globals.TIME_LIMIT
        self.progress["value"] = globals.TIME_LIMIT
        self.update_timer_label()
        self.timer_running = True
        self.countdown()

    def countdown(self):
        if not self.timer_running:
            return
        self.time_left -= 0.1
        self.time_left = max(0, self.time_left)
        self.update_timer_label()
        self.progress["value"] = self.time_left

        if self.time_left <= 0:
            self.timer_running = False
            self.disable_answers()
            self.show_feedback(correct=False, timed_out=True)
        else:
            self.root.after(100, self.countdown)

    def update_timer_label(self):
        self.time_label.config(text=self.t("time_left").format(self.time_left))

    def disable_answers(self):
        for btn in self.answer_buttons.values():
            btn.config(state="disabled")

    def answer_selected(self):
        if not self.timer_running:
            return
        self.timer_running = False
        selected = self.answer_var.get()
        q = self.questions[self.current_question_index]
        self.disable_answers()

        if selected == q["correct"]:
            self.correct_answers += 1
            self.show_feedback(correct=True)
            if platform.system() == "Windows":
                winsound.MessageBeep(winsound.MB_OK)
        else:
            self.show_feedback(correct=False)

    def show_feedback(self, correct, timed_out=False):
        q = self.questions[self.current_question_index]
        correct_option = q["correct"]
        correct_text = f"{correct_option}) {q['options'][correct_option]}"

        if correct:
            self.feedback_label.config(text=self.t("correct"), fg="green")
            self.answer_buttons[correct_option].config(bg="lightgreen")
        else:
            if timed_out:
                self.feedback_label.config(text=self.t("incorrect").format(correct_text), fg="red")
            else:
                self.feedback_label.config(text=self.t("incorrect").format(correct_text), fg="red")
            self.answer_buttons[correct_option].config(bg="lightgreen")
            selected = self.answer_var.get()
            if selected in self.answer_buttons:
                self.answer_buttons[selected].config(bg="lightcoral")

        self.next_button.config(state="normal")

    def blink_feedback(self, color):
        # Animacja błysku całego okna na kolor zielony lub czerwony
        def flash(times):
            if times <= 0:
                self.root.config(bg="SystemButtonFace" if platform.system() == "Windows" else "lightgrey")
                return
            self.root.config(bg=color)
            self.root.after(150, lambda: self.root.config(bg="SystemButtonFace" if platform.system() == "Windows" else "lightgrey"))
            self.root.after(300, lambda: flash(times - 1))
        flash(2)

    def next_question(self):
        self.next_button.config(state="disabled")
        self.current_question_index += 1
        if self.current_question_index >= len(self.questions):
            self.show_results()
            return
        self.load_question(self.current_question_index)

    def show_results(self):
        for w in self.root.winfo_children():
            w.destroy()
        duration = round(time.time() - self.start_time, 2)
        # Zapis wyników
        cursor.execute("INSERT INTO scores (nickname, category, score, total, duration, language) VALUES (?, ?, ?, ?, ?, ?)",
                       (self.nickname, self.category, self.correct_answers, len(self.questions), duration, self.language))
        conn.commit()

        tk.Label(self.root, text=self.t("result").format(self.correct_answers, len(self.questions)), font=("Arial", 24)).pack(pady=20)
        tk.Label(self.root, text=self.t("time").format(duration), font=("Arial", 18)).pack(pady=10)

        # Ranking
        cursor.execute("SELECT id, score, nickname FROM scores WHERE category = ? AND language = ? ORDER BY score DESC, duration ASC LIMIT 10",
                       (self.category, self.language))
        scores = cursor.fetchall()
        rank = next((i + 1 for i, s in enumerate(scores) if s[2] == self.nickname and s[1] == self.correct_answers), None)

        if rank:
            tk.Label(self.root, text=self.t("rank").format(rank), font=("Arial", 16)).pack(pady=10)

        tk.Label(self.root, text=self.t("top_scores"), font=("Arial", 16, "underline")).pack(pady=10)
        for i, (id_, score, nick) in enumerate(scores, 1):
            tk.Label(self.root, text=f"{i}. {nick}: {score}", font=("Arial", 14)).pack()

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text=self.t("play_again"), font=("Arial", 14), command=self.ask_language_mode_screen).pack(side="left", padx=20)
        tk.Button(btn_frame, text=self.t("exit"), font=("Arial", 14), command=self.root.quit).pack(side="left", padx=20)
