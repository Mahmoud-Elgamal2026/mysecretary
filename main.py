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

def get_main_keyboard():
    keyboard = [
        [KeyboardButton("📋 مهامي"), KeyboardButton("➕ مهمة جديدة")],
        [KeyboardButton("📅 مواعيدي"), KeyboardButton("📧 إيميلاتي")],
        [KeyboardButton("🌤️ الطقس"), KeyboardButton("💬 تحدث معايا")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

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

def add_task(task, priority="متوسطة", deadline="", notes="", reminder="60"):
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
            body={'values': [[task_num, task, priority, "جديدة", now, "", "", reminder, deadline, notes]]}
        ).execute()
        return f"✅ تمت إضافة المهمة: {task}"
    except Exception as e:
        return f"مش قادر أضيف: {e}"

def update_task_status(task_num, status):
    try:
        creds = get_google_creds()
        service = build('sheets', 'v4', credentials=creds)
        now = datetime.now(pytz.timezone('Africa/Cairo')).strftime("%Y-%m-%d %H:%M")
        # task_num هنا هو رقم المهمة في القائمة (يبدأ من 1)
        # في الشيت السطر = task_num + 1 (عشان الهيدر)
        row_index = task_num + 1
        service.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=f'{TASKS_SHEET}!D{row_index}',
            valueInputOption='RAW',
            body={'values': [[status]]}
        ).execute()
        if status == "✅ منتهية":
            service.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range=f'{TASKS_SHEET}!G{row_index}',
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
        # task_num يبدأ من 1، في الشيت السطر الأول هو الهيدر (index 0)
        # يعني مهمة رقم 1 هي في index 1
        row_index = task_num
        service.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={'requests': [{'deleteDimension': {'range': {
                'sheetId': sheet_id,
                'dimension': 'ROWS',
                'startIndex': row_index,
                'endIndex': row_index + 1
            }}}]}
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
        result = service.spreadsheets().values().get(spreadsheetId=SHEET_ID, range=f'{TASKS_SHEET}!A:A').execute()
        rows = result.get('values', [])
        if len(rows) <= 1:
            return "مفيش مهام تتحذف"
        service.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={'requests': [{'deleteDimension': {'range': {
                'sheetId': sheet_id,
                'dimension': 'ROWS',
                'startIndex': 1,
                'endIndex': len(rows)
            }}}]}
        ).execute()
        return "✅ تم حذف كل المهام!"
    except Exception as e:
        return f"مش قادر أحذف: {e}"

def get_gmail_summary():
    try:
        creds = get_google_creds()
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().messages().list(userId='me', labelIds=['INBOX', 'UNREAD'], maxResults=5).execute()
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
        events_result = service.events().list(calendarId='primary', timeMin=now, maxResults=5, singleEvents=True, orderBy='startTime').execute()
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
    months_ar = ["يناير", "فبراير", "مارس", "إبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
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

def get_status_bar():
    day_name, date_str, time_str = get_datetime()
    weather = get_weather()
    hijri = get_hijri_date()
    return f"📅 {day_name} {date_str} | {hijri}\n🕐 {time_str} | 🌡️ {weather}"

async def check_task_reminders(context):
    if not MAHMOUD_CHAT_ID:
        return
    try:
        creds = get_google_creds()
        service = build('sheets', 'v4', credentials=creds)
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=f'{TASKS_SHEET}!A:J'
        ).execute()
        rows = result.get('values', [])
        if len(rows) <= 1:
            return
        egypt_tz = pytz.timezone('Africa/Cairo')
        now = datetime.now(egypt_tz)
        for row in rows[1:]:
            if len(row) < 9:
                continue
            task_name = row[1] if len(row) > 1 else ""
            status = row[3] if len(row) > 3 else ""
            reminder_str = row[7] if len(row) > 7 else "60"
            deadline_str = row[8] if len(row) > 8 else ""
            if not deadline_str or status in ["✅ منتهية"] or not reminder_str or reminder_str == "0":
                continue
            try:
                reminder_minutes = int(reminder_str)
                deadline = datetime.strptime(deadline_str, "%Y-%m-%d").replace(tzinfo=egypt_tz)
                diff_minutes = (deadline - now).total_seconds() / 60
                if reminder_minutes - 1 <= diff_minutes <= reminder_minutes + 1:
                    await context.bot.send_message(
                        chat_id=MAHMOUD_CHAT_ID,
                        text=f"🔔 تنبيه يا محمود!\n\nالمهمة: *{task_name}*\nموعدها بعد {reminder_minutes} دقيقة! ⏰",
                        parse_mode='Markdown',
                        reply_markup=get_main_keyboard()
                    )
            except:
                continue
    except Exception as e:
        print(f"خطأ في التنبيهات: {e}")

async def start_add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global pending_task
    pending_task = {}
    await update.message.reply_text("✍️ اكتب اسم المهمة:")
    return TASK_NAME

async def get_task_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pending_task['name'] = update.message.text
    keyboard = [
        [InlineKeyboardButton("🔴 عالية", callback_data="priority_عالية"),
         InlineKeyboardButton("🟡 متوسطة", callback_data="priority_متوسطة"),
         InlineKeyboardButton("🟢 منخفضة", callback_data="priority_منخفضة")]
    ]
    await update.message.reply_text(
        f"✅ المهمة: *{pending_task['name']}*\n\nاختار الأولوية:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TASK_PRIORITY

async def get_task_priority(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pending_task['priority'] = query.data.replace("priority_", "")
    egypt_tz = pytz.timezone('Africa/Cairo')
    today = datetime.now(egypt_tz).strftime("%Y-%m-%d")
    tomorrow = (datetime.now(egypt_tz) + timedelta(days=1)).strftime("%Y-%m-%d")
    next_week = (datetime.now(egypt_tz) + timedelta(days=7)).strftime("%Y-%m-%d")
    keyboard = [
        [InlineKeyboardButton("📅 النهارده", callback_data=f"deadline_{today}"),
         InlineKeyboardButton("📅 بكره", callback_data=f"deadline_{tomorrow}")],
        [InlineKeyboardButton("📅 الأسبوع الجاي", callback_data=f"deadline_{next_week}"),
         InlineKeyboardButton("✍️ اكتب تاريخ", callback_data="deadline_custom")],
        [InlineKeyboardButton("⏭️ بدون موعد", callback_data="deadline_none")]
    ]
    await query.edit_message_text(
        f"✅ المهمة: *{pending_task['name']}*\n🎯 الأولوية: {pending_task['priority']}\n\nاختار الموعد النهائي:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TASK_DEADLINE

async def get_task_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.replace("deadline_", "")
    if data == "custom":
        await query.edit_message_text("✍️ اكتب الموعد النهائي (مثال: 2026-05-10):")
        return TASK_CUSTOM_DEADLINE
    pending_task['deadline'] = "" if data == "none" else data
    keyboard = [
        [InlineKeyboardButton("⏰ 10 دقائق", callback_data="reminder_10"),
         InlineKeyboardButton("⏰ 30 دقيقة", callback_data="reminder_30")],
        [InlineKeyboardButton("⏰ ساعة", callback_data="reminder_60"),
         InlineKeyboardButton("⏰ ساعتين", callback_data="reminder_120")],
        [InlineKeyboardButton("⏰ يوم كامل", callback_data="reminder_1440"),
         InlineKeyboardButton("✍️ وقت مخصص", callback_data="reminder_custom")],
        [InlineKeyboardButton("🔕 بدون تنبيه", callback_data="reminder_none")]
    ]
    await query.edit_message_text(
        f"✅ المهمة: *{pending_task['name']}*\n🎯 الأولوية: {pending_task['priority']}\n📅 الموعد: {pending_task['deadline'] or 'بدون موعد'}\n\nاختار وقت التنبيه:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TASK_REMINDER

async def get_custom_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pending_task['deadline'] = update.message.text
    keyboard = [
        [InlineKeyboardButton("⏰ 10 دقائق", callback_data="reminder_10"),
         InlineKeyboardButton("⏰ 30 دقيقة", callback_data="reminder_30")],
        [InlineKeyboardButton("⏰ ساعة", callback_data="reminder_60"),
         InlineKeyboardButton("⏰ ساعتين", callback_data="reminder_120")],
        [InlineKeyboardButton("⏰ يوم كامل", callback_data="reminder_1440"),
         InlineKeyboardButton("✍️ وقت مخصص", callback_data="reminder_custom")],
        [InlineKeyboardButton("🔕 بدون تنبيه", callback_data="reminder_none")]
    ]
    await update.message.reply_text(
        f"✅ المهمة: *{pending_task['name']}*\n🎯 الأولوية: {pending_task['priority']}\n📅 الموعد: {pending_task['deadline']}\n\nاختار وقت التنبيه:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TASK_REMINDER

async def get_task_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.replace("reminder_", "")
    if data == "none":
        pending_task['reminder'] = "0"
    elif data == "custom":
        await query.edit_message_text("✍️ اكتب وقت التنبيه بالدقائق (مثال: 45):")
        return TASK_NOTES
    else:
        pending_task['reminder'] = data
    keyboard = [[InlineKeyboardButton("⏭️ بدون ملاحظات", callback_data="notes_none")]]
    reminder_text = {"0": "بدون تنبيه", "10": "10 دقائق", "30": "30 دقيقة", "60": "ساعة", "120": "ساعتين", "1440": "يوم كامل"}.get(pending_task['reminder'], f"{pending_task['reminder']} دقيقة")
    await query.edit_message_text(
        f"✅ المهمة: *{pending_task['name']}*\n🎯 الأولوية: {pending_task['priority']}\n📅 الموعد: {pending_task.get('deadline', '') or 'بدون موعد'}\n⏰ التنبيه: {reminder_text}\n\nاكتب ملاحظات أو اضغط بدون ملاحظات:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TASK_NOTES

async def get_task_notes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pending_task['notes'] = ""
    result = add_task(pending_task['name'], pending_task['priority'], pending_task.get('deadline', ''), pending_task['notes'], pending_task.get('reminder', '60'))
    await query.edit_message_text(f"{get_status_bar()}\n{'─'*30}\n{result}")
    return ConversationHandler.END

async def get_task_notes_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'reminder' not in pending_task:
        pending_task['reminder'] = update.message.text
        keyboard = [[InlineKeyboardButton("⏭️ بدون ملاحظات", callback_data="notes_none")]]
        await update.message.reply_text(
            f"✅ التنبيه: {pending_task['reminder']} دقيقة\n\nاكتب ملاحظات أو اضغط بدون ملاحظات:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return TASK_NOTES
    pending_task['notes'] = update.message.text
    result = add_task(pending_task['name'], pending_task['priority'], pending_task.get('deadline', ''), pending_task['notes'], pending_task.get('reminder', '60'))
    await update.message.reply_text(f"{get_status_bar()}\n{'─'*30}\n{result}", reply_markup=get_main_keyboard())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم الإلغاء!", reply_markup=get_main_keyboard())
    return ConversationHandler.END

async def daily_reminder(context):
    if MAHMOUD_CHAT_ID:
        tasks = get_tasks()
        calendar = get_calendar_events()
        msg = f"🌅 صباح الخير يا محمود!\n\n📋 مهامك النهارده:\n{tasks}\n\n📆 مواعيدك:\n{calendar}"
        await context.bot.send_message(chat_id=MAHMOUD_CHAT_ID, text=msg, reply_markup=get_main_keyboard())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global MAHMOUD_CHAT_ID
    MAHMOUD_CHAT_ID = update.message.chat_id
    user_text = update.message.text
    status_bar = get_status_bar()

    if user_text == "📋 مهامي":
        tasks = get_tasks()
        await update.message.reply_text(f"{status_bar}\n{'─'*30}\n📋 مهامك:\n{tasks}", reply_markup=get_main_keyboard())
        return
    elif user_text == "➕ مهمة جديدة":
        await start_add_task(update, context)
        return
    elif user_text == "📅 مواعيدي":
        calendar = get_calendar_events()
        await update.message.reply_text(f"{status_bar}\n{'─'*30}\n📅 مواعيدك:\n{calendar}", reply_markup=get_main_keyboard())
        return
    elif user_text == "📧 إيميلاتي":
        gmail = get_gmail_summary()
        await update.message.reply_text(f"{status_bar}\n{'─'*30}\n📧 {gmail}", reply_markup=get_main_keyboard())
        return
    elif user_text == "🌤️ الطقس":
        weather = get_weather()
        await update.message.reply_text(f"{status_bar}\n{'─'*30}\n🌤️ الطقس: {weather}", reply_markup=get_main_keyboard())
        return

    calendar = get_calendar_events()
    gmail = get_gmail_summary()
    tasks = get_tasks()

    conversation_history.append({"role": "user", "content": user_text})
    if len(conversation_history) > 20:
        conversation_history.pop(0)

    system_prompt = f"""أنت سكرتير محمود الشخصي، ذكي وفرفوش وبترد بلهجة مصرية عامية شيك.
ناديه دايماً بـ "محمود".
لو طلب ترجمة، ترجملهوله على طول.
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
        response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages)
        bot_response = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": bot_response})
        first_line = bot_response.strip().split("\n")[0].strip()

        if first_line.startswith("COMPLETE_TASK:"):
            num = int(first_line.replace("COMPLETE_TASK:", "").strip())
            result = update_task_status(num, "✅ منتهية")
            await update.message.reply_text(f"{status_bar}\n{'─'*30}\n{result}", reply_markup=get_main_keyboard())
        elif first_line.startswith("PAUSE_TASK:"):
            num = int(first_line.replace("PAUSE_TASK:", "").strip())
            result = update_task_status(num, "⏸️ موقوفة")
            await update.message.reply_text(f"{status_bar}\n{'─'*30}\n{result}", reply_markup=get_main_keyboard())
        elif first_line.startswith("START_TASK:"):
            num = int(first_line.replace("START_TASK:", "").strip())
            result = update_task_status(num, "🔄 شغال")
            await update.message.reply_text(f"{status_bar}\n{'─'*30}\n{result}", reply_markup=get_main_keyboard())
        elif first_line.startswith("DELETE_TASK:"):
            num = int(first_line.replace("DELETE_TASK:", "").strip())
            result = delete_task(num)
            await update.message.reply_text(f"{status_bar}\n{'─'*30}\n{result}", reply_markup=get_main_keyboard())
        elif "DELETE_ALL_TASKS" in first_line:
            result = delete_all_tasks()
            await update.message.reply_text(f"{status_bar}\n{'─'*30}\n{result}", reply_markup=get_main_keyboard())
        else:
            await update.message.reply_text(f"{status_bar}\n{'─'*30}\n{bot_response}", reply_markup=get_main_keyboard())

    except Exception as e:
        print(f"خطأ: {e}")
        await update.message.reply_text("حصل دروب يا محمود، بعت تاني!", reply_markup=get_main_keyboard())

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("➕ مهمة جديدة"), start_add_task)],
        states={
            TASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_task_name)],
            TASK_PRIORITY: [CallbackQueryHandler(get_task_priority, pattern="^priority_")],
            TASK_DEADLINE: [CallbackQueryHandler(get_task_deadline, pattern="^deadline_")],
            TASK_CUSTOM_DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_custom_deadline)],
            TASK_REMINDER: [CallbackQueryHandler(get_task_reminder, pattern="^reminder_")],
            TASK_NOTES: [
                CallbackQueryHandler(get_task_notes_callback, pattern="^notes_none"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_task_notes_text)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    egypt_tz = pytz.timezone('Africa/Cairo')
    app.job_queue.run_daily(
        daily_reminder,
        time=datetime.strptime("08:00", "%H:%M").time().replace(tzinfo=egypt_tz)
    )
    app.job_queue.run_repeating(check_task_reminders, interval=60, first=10)

    print("البوت شغال يا محمود!")
    app.run_polling()

if __name__ == "__main__":
    main()
