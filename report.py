import os
import datetime
import requests
import pytz

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

tz = pytz.timezone("Europe/Moscow")
now = datetime.datetime.now(tz).strftime("%d.%m.%Y %H:%M")

def build_report():
    return f"""📊 Ежедневный отчёт на {now}

Москва: ...
Россия: ...
США: ...
Европа: ...
Азия: ...
Ближний Восток: ...
🤖 Роботы: ...
🔬 Наука: ...

🧭 Общий вывод: ...
"""

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

if __name__ == "__main__":
    report = build_report()
    send_message(report)
