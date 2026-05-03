from groq import Groq
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import requests
from datetime import datetime
import pytz
import os
import imaplib
import email
from email.header import decode_header
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json

TELEGRAM_TOKEN = "8569606909:AAEdLS1E5aruUZW60EPDThrWyGIsCUQlBNs"
GROQ_KEY = "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"
WEATHER_KEY = "4878e67a8ae538cb3737137a422ccdc9"
GMAIL_USER = os.environ.get('GMAIL_USER', 'prof.mahmoud2016@gmail.com')
GMAIL_PASSWORD = os.environ.get('GMAIL_PASSWORD', '')

client = Groq(api_key=GROQ_KEY)
conversation_history = []

def get_gmail_summary():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASSWORD)
        mail.select("inbox")
        _, messages = mail.search(None, 'UNSEEN')
        email_ids = messages[0].split()
        if not email_ids:
            return "مفيش إيميلات جديدة"
        result = f"عندك {len(email_ids)} إيميل جديد:\n"
        for eid in email_ids[-5:]:
            _, msg_data = mail.fetch(eid, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            subject = decode_header(msg["Subject"])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode(errors='ignore')
            sender = msg.get("From", "")
            result += f"• من: {sender}\n  الموضوع: {subject}\n"
        mail.logout()
        return result
    except Exception as e:
        return f"مش قادر اوصل للإيميل: {e}"

def get_google_creds():
    token_data = json.loads(os.environ.get('GOOGLE_TOKEN', '{}'))
    creds = Credentials(
        token=token_data.get('token'),
        refresh_token=token_data.get('refresh_token'),
        token_uri=token_data.get('token_uri'),
        client_id=token_data.get('client_id'),
        client_secret=token_data.get('client_secret'),
        scopes=token_data.get('scopes')
    )
    return creds

def get_calendar_events():
    try:
        creds = get_google_creds()
        service = build('calendar', 'v3', credentials=creds)
        now = datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=5,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        if not events:
            return "مفيش مواعيد قادمة"
        result = ""
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            result += f"- {event['summary']} | {start}\n"
        return result
    except Exception as e:
        return f"مش قادر اوصل للكالندر: {e}"

def get_hijri_date():
    try:
        today = datetime.now().strftime("%d-%m-%Y")
        url = f"https://api.aladhan.com/v1/gToH/{today}"
        response = requests.get(url)
        data = response.json()
        hijri = data['data']['hijri']
        return f"{hijri['day']} {hijri['month']['ar']} {hijri['year']}هـ"
    except:
        return ""

def get_datetime():
    egypt_tz = pytz.timezone('Africa/Cairo')
    now = datetime.now(egypt_tz)
    days_ar = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
    months_ar = ["يناير", "فبراير", "مارس", "إبريل", "مايو", "يونيو",
                 "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
    day_name = days_ar[now.weekday()]
    date_str = f"{now.day} {months_ar[now.month-1]} {now.year}"
    time_str = now.strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م")
    return day_name, date_str, time_str

def get_weather():
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q=Cairo&appid={WEATHER_KEY}&units=metric&lang=ar"
        response = requests.get(url)
        data = response.json()
        temp = round(data['main']['temp'])
        desc = data['weather'][0]['description']
        return f"{temp}°C {desc}"
    except:
        return "مش متاح"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    day_name, date_str, time_str = get_datetime()
    weather = get_weather()
    hijri = get_hijri_date()
    calendar = get_calendar_events()
    gmail = get_gmail_summary()

    status_bar = f"📅 {day_name} {date_str} | {hijri}\n🕐 {time_str} | 🌡️ {weather}"

    conversation_history.append({"role": "user", "content": user_text})
    if len(conversation_history) > 20:
        conversation_history.pop(0)

    system_prompt = f"""أنت سكرتير محمود الشخصي، ذكي وفرفوش وبترد بلهجة مصرية عامية شيك.
ناديه دايماً بـ "محمود".
لو طلب ترجمة، ترجملهوله على طول.
المعلومات الحالية:
{status_bar}
📆 المواعيد القادمة:
{calendar}
📧 الإيميل: {gmail}"""

    messages = [{"role": "system", "content": system_prompt}] + conversation_history

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages
        )
        bot_response = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": bot_response})
        full_response = f"{status_bar}\n{'─'*30}\n{bot_response}"
        await update.message.reply_text(full_response)
    except Exception as e:
        print(f"خطأ: {e}")
        await update.message.reply_text("حصل دروب يا محمود، بعت تاني!")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("البوت شغال يا محمود!")
    app.run_polling()

if __name__ == "__main__":
    main()
