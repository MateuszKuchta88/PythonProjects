import openai
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def summarize_laws(laws):
    summaries = []
    for law in laws:
        print(f"Streszczam: {law['title']}")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Streszczaj nowe ustawy w prostym, zrozumiałym języku."},
                {"role": "user", "content": law["content"]}
            ]
        )
        summary = response["choices"][0]["message"]["content"]
        summaries.append({
            "title": law["title"],
            "summary": summary,
            "url": law["url"]
        })
    return summaries
