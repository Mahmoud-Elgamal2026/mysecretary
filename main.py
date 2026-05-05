from groq import Groq
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import requests
from datetime import datetime
import pytz
import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

TELEGRAM_TOKEN = "8569606909:AAEdLS1E5aruUZW60EPDThrWyGIsCUQlBNs"
GROQ_KEY = "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"
WEATHER_KEY = "4878e67a8ae538cb3737137a422ccdc9"
SHEET_ID = "18uJrVBBjOOg51sReKhXdxmZdWnBsuAhZlEBda6K8JG8"
TASKS_SHEET = "Tasks"
MAHMOUD_CHAT_ID = None

client = Groq(api_key=GROQ_KEY)
conversation_history = []

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
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds

def get_tasks():
    try:
        creds = get_google_creds()
        service = build('sheets', 'v4', credentials=creds)
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=f'{TASKS_SHEET}!A:J'
        ).execute()
        rows = result.get('values', [])
        if len(rows) <= 1:
            return "مفيش مهام دلوقتي"
        tasks = ""
        for i, row in enumerate(rows[1:], 1):
            task = row[1] if len(row) > 1 else ""
            priority = row[2] if len(row) > 2 else ""
            status = row[3] if len(row) > 3 else ""
            deadline = row[8] if len(row) > 8 else ""
            tasks += f"{i}. {task} | {priority} | {status} | {deadline}\n"
        return tasks
    except Exception as e:
        return f"مش قادر اوصل للمهام: {e}"

def add_task(task, priority="متوسطة", deadline="", notes=""):
    try:
        creds = get_google_creds()
        now = datetime.now(pytz.timezone('Africa/Cairo')).strftime("%Y-%m-%d %H:%M")
        sheets_service = build('sheets', 'v4', credentials=creds)
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=f'{TASKS_SHEET}!A:A'
        ).execute()
        rows = result.get('values', [])
        task_num = len(rows)
        sheets_service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range=f'{TASKS_SHEET}!A:J',
            valueInputOption='RAW',
            body={'values': [[task_num, task, priority, "جديدة", now, "", "", "", deadline, notes]]}
        ).execute()
        return f"✅ تمت إضافة المهمة: {task}"
    except Exception as e:
        return f"مش قادر أضيف: {e}"

def update_task_status(task_num, status):
    try:
        creds = get_google_creds()
        service = build('sheets', 'v4', credentials=creds)
        now = datetime.now(pytz.timezone('Africa/Cairo')).strftime("%Y-%m-%d %H:%M")
        service.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=f'{TASKS_SHEET}!D{task_num+1}',
            valueInputOption='RAW',
            body={'values': [[status]]}
        ).execute()
        if status == "✅ منتهية":
            service.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range=f'{TASKS_SHEET}!G{task_num+1}',
                valueInputOption='RAW',
                body={'values': [[now]]}
            ).execute()
        return f"✅ تم تحديث المهمة رقم {task_num} إلى: {status}"
    except Exception as e:
        return f"مش قادر أحدث: {e}"

def delete_task(task_num):
    try:
        creds = get_google_creds()
        service = build('sheets', 'v4', credentials=creds)
        sheet_metadata = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
        sheet_id = None
        for sheet in sheet_metadata['sheets']:
            if sheet['properties']['title'] == TASKS_SHEET:
                sheet_id = sheet['properties']['sheetId']
                break
        service.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={
                'requests': [{
                    'deleteDimension': {
                        'range': {
                            'sheetId': sheet_id,
                            'dimension': 'ROWS',
                            'startIndex': task_num,
                            'endIndex': task_num + 1
                        }
                    }
                }]
            }
        ).execute()
        return f"✅ تم حذف المهمة رقم {task_num}"
    except Exception as e:
        return f"مش قادر أحذف: {e}"

def delete_all_tasks():
    try:
        creds = get_google_creds()
        service = build('sheets', 'v4', credentials=creds)
        sheet_metadata = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
        sheet_id = None
        for sheet in sheet_metadata['sheets']:
            if sheet['properties']['title'] == TASKS_SHEET:
                sheet_id = sheet['properties']['sheetId']
                break
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=f'{TASKS_SHEET}!A:A'
        ).execute()
        rows = result.get('values', [])
        if len(rows) <= 1:
            return "مفيش مهام تتحذف"
        service.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={
                'requests': [{
                    'deleteDimension': {
                        'range': {
                            'sheetId': sheet_id,
                            'dimension': 'ROWS',
                            'startIndex': 1,
                            'endIndex': len(rows)
                        }
                    }
                }]
            }
        ).execute()
        return "✅ تم حذف كل المهام!"
    except Exception as e:
        return f"مش قادر أحذف: {e}"

def get_gmail_summary():
    try:
        creds = get_google_creds()
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().messages().list(
            userId='me',
            labelIds=['INBOX', 'UNREAD'],
            maxResults=5
        ).execute()
        messages = results.get('messages', [])
        if not messages:
            return "مفيش إيميلات جديدة"
        return f"عندك {len(messages)} إيميل جديد"
    except Exception as e:
        return f"مش قادر اوصل للإيميل: {e}"

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

async def daily_reminder(context):
    if MAHMOUD_CHAT_ID:
        tasks = get_tasks()
        calendar = get_calendar_events()
        msg = f"🌅 صباح الخير يا محمود!\n\n📋 مهامك النهارده:\n{tasks}\n\n📆 مواعيدك:\n{calendar}"
        await context.bot.send_message(chat_id=MAHMOUD_CHAT_ID, text=msg)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global MAHMOUD_CHAT_ID
    MAHMOUD_CHAT_ID = update.message.chat_id
    user_text = update.message.text
    day_name, date_str, time_str = get_datetime()
    weather = get_weather()
    hijri = get_hijri_date()
    calendar = get_calendar_events()
    gmail = get_gmail_summary()
    tasks = get_tasks()

    status_bar = f"📅 {day_name} {date_str} | {hijri}\n🕐 {time_str} | 🌡️ {weather}"

    conversation_history.append({"role": "user", "content": user_text})
    if len(conversation_history) > 20:
        conversation_history.pop(0)

    system_prompt = f"""أنت سكرتير محمود الشخصي، ذكي وفرفوش وبترد بلهجة مصرية عامية شيك.
ناديه دايماً بـ "محمود".
لو طلب ترجمة، ترجملهوله على طول.
لو طلب إضافة مهمة، ردك يكون بالضبط على السطر الأول فقط: ADD_TASK:[اسم المهمة فقط]
لو قال خلصت مهمة [رقم]: COMPLETE_TASK:[رقم]
لو قال وقفت مهمة [رقم]: PAUSE_TASK:[رقم]
لو قال شغال على مهمة [رقم]: START_TASK:[رقم]
لو قال احذف مهمة [رقم]: DELETE_TASK:[رقم]
لو قال احذف كل المهام: DELETE_ALL_TASKS
المعلومات الحالية:
{status_bar}
📆 المواعيد القادمة:
{calendar}
📧 الإيميل: {gmail}
📋 المهام:
{tasks}"""

    messages = [{"role": "system", "content": system_prompt}] + conversation_history

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages
        )
        bot_response = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": bot_response})

        first_line = bot_response.strip().split("\n")[0].strip()

        if first_line.startswith("ADD_TASK:"):
            task = first_line.replace("ADD_TASK:", "").strip()
            result = add_task(task)
            await update.message.reply_text(f"{status_bar}\n{'─'*30}\n{result}")
        elif first_line.startswith("COMPLETE_TASK:"):
            num = int(first_line.replace("COMPLETE_TASK:", "").strip())
            result = update_task_status(num, "✅ منتهية")
            await update.message.reply_text(f"{status_bar}\n{'─'*30}\n{result}")
        elif first_line.startswith("PAUSE_TASK:"):
            num = int(first_line.replace("PAUSE_TASK:", "").strip())
            result = update_task_status(num, "⏸️ موقوفة")
            await update.message.reply_text(f"{status_bar}\n{'─'*30}\n{result}")
        elif first_line.startswith("START_TASK:"):
            num = int(first_line.replace("START_TASK:", "").strip())
            result = update_task_status(num, "🔄 شغال")
            await update.message.reply_text(f"{status_bar}\n{'─'*30}\n{result}")
        elif first_line.startswith("DELETE_TASK:"):
            num = int(first_line.replace("DELETE_TASK:", "").strip())
            result = delete_task(num)
            await update.message.reply_text(f"{status_bar}\n{'─'*30}\n{result}")
        elif "DELETE_ALL_TASKS" in first_line:
            result = delete_all_tasks()
            await update.message.reply_text(f"{status_bar}\n{'─'*30}\n{result}")
        else:
            full_response = f"{status_bar}\n{'─'*30}\n{bot_response}"
            await update.message.reply_text(full_response)

    except Exception as e:
        print(f"خطأ: {e}")
        await update.message.reply_text("حصل دروب يا محمود، بعت تاني!")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    egypt_tz = pytz.timezone('Africa/Cairo')
    app.job_queue.run_daily(
        daily_reminder,
        time=datetime.strptime("08:00", "%H:%M").time().replace(tzinfo=egypt_tz)
    )
    print("البوت شغال يا محمود!")
    app.run_polling()

if __name__ == "__main__":
    main()
