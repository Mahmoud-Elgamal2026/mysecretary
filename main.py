from groq import Groq
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, MessageHandler, filters, ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler
import requests
from datetime import datetime, timedelta
import pytz
import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# --- الإعدادات (تأكد من صحتها يا محمود) ---
TELEGRAM_TOKEN = "8569606909:AAEdLS1E5aruUZW60EPDThrWyGIsCUQlBNs"
GROQ_KEY = "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"
WEATHER_KEY = "4878e67a8ae538cb3737137a422ccdc9"
SHEET_ID = "18uJrVBBjOOg51sReKhXdxmZdWnBsuAhZlEBda6K8JG8"
TASKS_SHEET = "Tasks"
MAHMOUD_CHAT_ID = None

TASK_NAME, TASK_PRIORITY, TASK_DEADLINE, TASK_CUSTOM_DEADLINE, TASK_NOTES, TASK_REMINDER = range(6)

client = Groq(api_key=GROQ_KEY)
conversation_history = []
pending_task = {}

# --- الدوال المساعدة ---

def get_main_keyboard():
    keyboard = [
        [KeyboardButton("📋 مهامي"), KeyboardButton("➕ مهمة جديدة")],
        [KeyboardButton("📅 مواعيدي"), KeyboardButton("📧 إيميلاتي")],
        [KeyboardButton("🌤️ الطقس"), KeyboardButton("💬 تحدث معايا")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_google_creds():
    # محاولة جلب التوكن من متغيرات البيئة
    token_env = os.environ.get('GOOGLE_TOKEN')
    if not token_env:
        return None
    
    token_data = json.loads(token_env)
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

def get_sheet_id_by_name(service, name):
    sheet_metadata = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    for sheet in sheet_metadata['sheets']:
        if sheet['properties']['title'] == name:
            return sheet['properties']['sheetId']
    return None

# --- دوال التعامل مع الشيت ---

def get_tasks():
    try:
        creds = get_google_creds()
        if not creds: return "❌ مشكلة في الوصول لـ Google Token"
        
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
            task = row[1] if len(row) > 1 else "بدون عنوان"
            priority = row[2] if len(row) > 2 else "-"
            status = row[3] if len(row) > 3 else "-"
            deadline = row[8] if len(row) > 8 else "-"
            tasks += f"{i}. {task} | {priority} | {status} | {deadline}\n"
        return tasks
    except Exception as e:
        return f"⚠️ خطأ في الشيت: {e}"

def add_task(task, priority="متوسطة", deadline="", notes="", reminder="60"):
    try:
        creds = get_google_creds()
        now = datetime.now(pytz.timezone('Africa/Cairo')).strftime("%Y-%m-%d %H:%M")
        sheets_service = build('sheets', 'v4', credentials=creds)
        
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f'{TASKS_SHEET}!A:A'
        ).execute()
        rows = result.get('values', [])
        task_num = len(rows)
        
        sheets_service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range=f'{TASKS_SHEET}!A:J',
            valueInputOption='RAW',
            body={'values': [[task_num, task, priority, "جديدة", now, "", "", reminder, deadline, notes]]}
        ).execute()
        return f"✅ تمت إضافة المهمة: {task}"
    except Exception as e:
        return f"❌ فشل الإضافة: {e}"

def delete_task(task_num):
    try:
        creds = get_google_creds()
        service = build('sheets', 'v4', credentials=creds)
        sheet_id = get_sheet_id_by_name(service, TASKS_SHEET)
        # مسح الصف (الرقم المدخل + 1 لأن الهيدر في الصف 0)
        row_index = int(task_num)
        service.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={'requests': [{'deleteDimension': {'range': {
                'sheetId': sheet_id, 'dimension': 'ROWS',
                'startIndex': row_index, 'endIndex': row_index + 1
            }}}]}
        ).execute()
        return f"✅ تم حذف المهمة رقم {task_num}"
    except Exception as e:
        return f"❌ فشل الحذف: {e}"

# --- دوال البيانات الإضافية ---

def get_datetime():
    egypt_tz = pytz.timezone('Africa/Cairo')
    now = datetime.now(egypt_tz)
    days_ar = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
    months_ar = ["يناير", "فبراير", "مارس", "إبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
    return days_ar[now.weekday()], f"{now.day} {months_ar[now.month-1]} {now.year}", now.strftime("%I:%M %p")

def get_weather():
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q=Cairo&appid={WEATHER_KEY}&units=metric&lang=ar"
        data = requests.get(url).json()
        return f"{round(data['main']['temp'])}°C {data['weather'][0]['description']}"
    except: return "غير متاح"

def get_status_bar():
    day, date, time = get_datetime()
    return f"📅 {day} {date} | 🌡️ {get_weather()}\n🕐 {time}"

# --- معالجة الرسائل والذكاء الاصطناعي ---

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global MAHMOUD_CHAT_ID
    MAHMOUD_CHAT_ID = update.message.chat_id
    user_text = update.message.text
    status_bar = get_status_bar()

    # الأوامر المباشرة
    if user_text == "📋 مهامي":
        await update.message.reply_text(f"{status_bar}\n{'-'*20}\n{get_tasks()}")
        return
    elif user_text == "🌤️ الطقس":
        await update.message.reply_text(f"الطقس دلوقتي في القاهرة: {get_weather()}")
        return

    # المحادثة مع AI
    conversation_history.append({"role": "user", "content": user_text})
    
    system_prompt = f"أنت سكرتير محمود الشخصي، رد بلهجة مصرية شيك. المعلومات الحالية:\n{status_bar}\nالمهام:\n{get_tasks()}"
    messages = [{"role": "system", "content": system_prompt}] + conversation_history[-10:]

    try:
        response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages)
        bot_response = response.choices[0].message.content
        
        # تنفيذ أوامر الحذف أو الإتمام لو طلب الـ AI ذلك (بناءً على الـ Prompt)
        if "DELETE_TASK:" in bot_response:
            task_num = bot_response.split("DELETE_TASK:")[1].strip().split()[0]
            bot_response = delete_task(task_num)

        await update.message.reply_text(bot_response, reply_markup=get_main_keyboard())
        conversation_history.append({"role": "assistant", "content": bot_response})

    except Exception as e:
        print(f"خطأ: {e}")
        await update.message.reply_text(f"حصل دروب يا محمود، السبب: {e}")

# --- تشغيل البوت ---

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # إضافة معالجة الرسائل
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("البوت شغال يا محمود..")
    app.run_polling()

if __name__ == "__main__":
    main()
