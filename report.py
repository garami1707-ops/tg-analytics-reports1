import os, datetime, pytz, requests, time, sys, json

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
KIND = os.getenv("KIND", "daily")  # daily | weekly | monthly

if not BOT_TOKEN or not CHAT_ID:
    print("❌ Нет BOT_TOKEN или CHAT_ID")
    sys.exit(1)

# -------- Telegram helpers --------
def send_telegram(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(url, data={"chat_id": CHAT_ID, "text": text})
    if r.status_code != 200:
        print("Ошибка Telegram:", r.text)
    return r

def send_long(text: str):
    MAX_LEN = 4000
    parts = [text[i:i+MAX_LEN] for i in range(0, len(text), MAX_LEN)]
    for i, part in enumerate(parts, 1):
        send_telegram(part)
        time.sleep(1.2)

# -------- Prompt builder --------
def build_prompt(today, kind):
    extra = ""
    if kind == "weekly":
        extra = "\nДобавь недельный обзор: что изменилось, связи, прогноз 4–12 недель."
    elif kind == "monthly":
        extra = "\nДобавь месячный обзор: ключевые тренды, причинно-следственные связи, прогноз 3–12 месяцев."
    return f"""
Ты — аналитик. Сформируй отчёт (дата: {today}) строго по формату:

1) Москва
   - свежие новости + контекст (факты, компании, продукты, суммы, сроки)
   - инфа с ресурсов (связка с новостями, если важно)
   - выводы на 6–24 мес.
2) Россия
3) США
4) Европа
5) Азия
6) Ближний Восток
7) 🤖 Роботы — тренды, новости, мини-выжимки из статей
8) 🔬 Наука и будущее — выжимки интересных исследований, открытий, планов
9) 🧭 Общий вывод — 15 пунктов «куда всё идёт сейчас».

Пиши подробно, с фактами, компаниями и примерами.{extra}
""".strip()

# -------- Report generator --------
def generate_report(kind="daily"):
    tz = pytz.timezone("Europe/Moscow")
    now = datetime.datetime.now(tz)
    today_str = now.strftime("%d.%m.%Y, %H:%M МСК")
    prompt = build_prompt(today_str, kind)

    if not OPENAI_API_KEY:
        return "⚠️ Нет OPENAI_API_KEY. Добавь его в Secrets → Actions."

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "gpt-4o-mini",  # можно заменить на другой
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": "Ты — строгий аналитик, отвечай фактами, структурно и интересно."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 3500
    }
    resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, data=json.dumps(data))
    if resp.status_code != 200:
        return f"⚠️ Ошибка API: {resp.status_code} {resp.text}"
    try:
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ Ошибка разбора ответа: {e}\nRAW: {resp.text}"

# -------- Main --------
if __name__ == "__main__":
    text = generate_report(KIND)
    send_long(text)
