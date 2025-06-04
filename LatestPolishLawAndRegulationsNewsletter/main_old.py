from scraper import get_new_laws

laws = get_new_laws()
if not laws:
    print("Brak nowych ustaw.")
else:
    print(f"Pierwsza ustawa: {laws[0]['title']}")
    print(laws[0]['content'][:2000])
