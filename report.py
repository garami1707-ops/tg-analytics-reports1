import os, datetime, time, pytz, textwrap, requests, sys

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID   = os.getenv("CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
KIND = os.getenv("KIND", "daily")  # daily | weekly | monthly

if not BOT_TOKEN or not CHAT_ID:
    print("Missing env: BOT_TOKEN or CHAT_ID")
    sys.exit(1)

def send_telegram(text: str):
    """Отправляет одно сообщение в Telegram."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(url, data={"chat_id": CHAT_ID, "text": text})
    if r.status_code != 200:
        print("TG error:", r.text)
    return r

def send_long(text: str):
    """Бережно режем длинный текст на части (<4096 симв.) и шлём по очереди."""
    MAX_LEN = 4000  # чуть меньше лимита
    parts = []
    buf = []
    total = 0
    for para in text.split("\n\n"):
        block = para.strip()
        if not block:
            continue
        # +2 за двойной перенос между параграфами
        if total + len(block) + 2 > MAX_LEN:
            parts.append("\n\n".join(buf))
            buf = [block]
            total = len(block)
        else:
            buf.append(block)
            total += len(block) + 2
    if buf:
        parts.append("\n\n".join(buf))
    # Отправляем с паузой
    for i, p in enumerate(parts, 1):
        send_telegram(p)
        time.sleep(1.2)

def build_prompt(today, kind):
    extra = ""
    if kind == "weekly":
        extra = "\nДобавь недельный синтез: что изменилось vs прошлой недели; связи; прогноз 4–12 недель."
    elif kind == "monthly":
        extra = "\nДобавь месячный мета-разбор: причинно-следственные связи; KPI; риски/возможности; прогноз 3–12 месяцев."
    return f"""
Ты — строгий аналитик. Сформируй СЕГОДНЯШНИЙ отчёт (дата: {today}) строго в формате:

1) Москва
   - сводка свежих новостей + контекст (факты, компании, суммы, сроки, продукты)
   - сводка информации с ресурсов (привязка к новостям, если важно)
   - аналитические выводы на 6–24 мес.
2) Россия
3) США
4) Европа
5) Азия
6) Ближний Восток
7) Роботы — ежедневная аналитика трендов/новостей + мини-выжимки из научных статей (и применимость)
8) Наука и будущее — выжимки интересных статей/открытий/планов: что показали → где применимо → горизонт
9) Общий вывод — 5–7 пунктов «куда всё идёт сейчас».

Пиши развернуто, с конкретными компаниями/продуктами/датами/суммами, но без «воды». Язык — русский.{extra}
""".strip()

def generate_report(kind="daily"):
    """Генерим отчёт через OpenAI. Требует OPENAI_API_KEY в секретах."""
    # Если ключ не задан — отправим внятную ошибку и не упадём
    if not OPENAI_API_KEY:
        return ("⚠️ OPENAI_API_KEY не задан. Добавь его в Secrets репозитория "
                "(Settings → Secrets → Actions). Тогда бот сможет собирать развёрнутую аналитику.")

    # Используем современный HTTP-вызов Chat Completions (без зависимостей на SDK)
    tz = pytz.timezone("Europe/Moscow")
    now = datetime.datetime.now(tz)
    today_str = now.strftime("%d.%m.%Y, %H:%M МСК")
    prompt = build_prompt(today_str, kind)

    import json
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "gpt-4o-mini",  # можешь поменять на свой
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": "Ты — аналитик. Отвечай структурно и фактурно."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 3500
    }
    # универсальная точка совместимости (если у тебя другой провайдер — замени endpoint)
    endpoint = "https://api.openai.com/v1/chat/completions"
    resp = requests.post(endpoint, headers=headers, data=json.dumps(data), timeout=120)
    if resp.status_code != 200:
        return f"⚠️ Не удалось сгенерировать отчёт: {resp.status_code} {resp.text}"
    j = resp.json()
    try:
        return j["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ Ошибка разбора ответа LLM: {e}\nRAW: {resp.text}"

if __name__ == "__main__":
    text = generate_report(KIND)
    send_long(text)
