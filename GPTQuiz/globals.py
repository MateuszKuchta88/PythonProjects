# ---------- Stałe ----------
QUESTION_COUNT = 5
TIME_LIMIT = 15.0  # sekund
PAUSE_BETWEEN_QUESTIONS = 1500  # ms
DB_NAME = "quiz_results.db"

# ---------- Lokalna baza pytań offline (PL i EN) ----------
LOCAL_QUESTIONS = {
    "PL": {
        "Historia Polski": [
            {
                "question": "Kto był pierwszym królem Polski?",
                "options": {"A": "Bolesław Chrobry", "B": "Mieszko I", "C": "Kazimierz Wielki",
                            "D": "Władysław Jagiełło"},
                "correct": "A",
                "image": None
            },
            {
                "question": "W którym roku rozpoczęła się II wojna światowa?",
                "options": {"A": "1938", "B": "1939", "C": "1940", "D": "1941"},
                "correct": "B",
                "image": None
            },
            # ... (możesz dodać więcej pytań)
        ],
        "Matematyka": [
            {
                "question": "Ile wynosi suma kątów wewnętrznych trójkąta?",
                "options": {"A": "90°", "B": "180°", "C": "270°", "D": "360°"},
                "correct": "B",
                "image": None
            },
        ]
    },
    "EN": {
        "Polish History": [
            {
                "question": "Who was the first king of Poland?",
                "options": {"A": "Bolesław Chrobry", "B": "Mieszko I", "C": "Casimir the Great",
                            "D": "Władysław Jagiełło"},
                "correct": "A",
                "image": None
            },
            {
                "question": "In which year did World War II start?",
                "options": {"A": "1938", "B": "1939", "C": "1940", "D": "1941"},
                "correct": "B",
                "image": None
            },
        ],
        "Math": [
            {
                "question": "What is the sum of the interior angles of a triangle?",
                "options": {"A": "90°", "B": "180°", "C": "270°", "D": "360°"},
                "correct": "B",
                "image": None
            },
        ]
    }
}