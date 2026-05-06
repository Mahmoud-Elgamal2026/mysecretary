import logging
import asyncio
import os
import json
from datetime import datetime
import pytz
from groq import Groq
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from google.oauth2 import service_account
from googleapiclient.discovery import build
from concurrent.futures import ThreadPoolExecutor

# 1. إعدادات الأمان واللوج
logging.basicConfig(level=logging.ERROR) # إظهار الأخطاء الحرجة فقط لمنع زحمة الكونسول
executor = ThreadPoolExecutor(max_workers=5) # محرك خارجي لتنفيذ المهام التقيلة بدون تهنيج

# --- الثوابت ---
TELEGRAM_TOKEN = "8569606909:AAEdLS1E5aruUZW60EPDThrWyGIsCUQlBNs"
GROQ_KEY = "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"
SHEET_ID = "18uJrVBBjOOg51sReKhXdxmZdWnBsuAhZlEBda6K8JG8"
TASKS_SHEET = "Tasks"

client = Groq(api_key=GROQ_KEY)
egypt_tz = pytz.timezone('Africa/Cairo')

# --- نظام جلب الصلاحيات المستقر ---
def get_service():
    try:
        # تأكد يا محمود إن ملف credentials.json موجود في نفس الفولدر
        path = 'credentials.json'
        if os.path.exists(path):
            creds = service_account.Credentials.from_service_account_file(
                path, scopes=['https://www.googleapis.com/auth/spreadsheets'])
            return build('sheets', 'v4', credentials=creds, cache_discovery=False)
    except: return None
    return None

# --- الدوال التنفيذية (بدون تأخير للشات) ---
def sync_get_tasks():
    service = get_service()
    if not service: return "مفيش اتصال بجوجل حالياً."
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f'{TASKS_SHEET}!A:J').execute()
        rows = result.get('values', [])
        if len(rows) <= 1: return "قائمة المهام فاضية."
        return "\n".join([f"- {r[1]} [{r[2]}]" for r in rows[1:6]]) # سحب آخر 5 مهام بس للخفة
    except: return "تعذر سحب المهام."

# --- معالجة الرسائل (القلب النابض للبوت) ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return

    user_text = update.message.text
    chat_id = update.effective_chat.id

    # إشعار "جاري المعالجة" لمنع إحساس التهنيج
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        # تشغيل سحب البيانات من جوجل و AI في Thread خارجي (عشان البوت ميفصلش)
        loop = asyncio.get_event_loop()
        
        # سحب المهام في الخلفية
        tasks_summary = await loop.run_in_executor(executor, sync_get_tasks)
        
        # بناء البرومبت
        system_msg = f"أنت سكرتير محمود المصري. الوقت: {datetime.now(egypt_tz).strftime('%H:%M')}. المهام: {tasks_summary}. رد بذكاء."
        
        # طلب الرد من Groq مع حماية من التأخير
        response = await loop.run_in_executor(executor, lambda: client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_text}
            ],
            timeout=20.0
        ))

        answer = response.choices[0].message.content
        await update.message.reply_text(answer)

    except Exception as e:
        # رد ذكي وبسيط في حالة الطوارئ بدل "الدروب"
        await update.message.reply_text("معاك يا محمود، بس جوجل مهنجة ثانية. اؤمرني محتاج إيه؟")

# --- التشغيل النهائي المضمون ---
def main():
    # استخدام drop_pending_updates لتنظيف البوت عند التشغيل
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # إضافة الأوامر الأساسية
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 السكرتير انطلق بأقصى سرعة وبدون تهنيج يا محمود!")
    
    # تشغيل مستقر مع معالجة رسايل الـ Close
    app.run_polling(drop_pending_updates=True, close_loop=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
