import logging
import asyncio
from datetime import datetime
import pytz
from groq import Groq
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- الإعدادات الأساسية يا محمود ---
TOKEN = "8569606909:AAEdLS1E5aruUZW60EPDThrWyGIsCUQlBNs"
GROQ_KEY = "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"
SHEET_ID = "18uJrVBBjOOg51sReKhXdxmZdWnBsuAhZlEBda6K8JG8"

# إعداد الـ AI والوقت
client = Groq(api_key=GROQ_KEY)
egypt_tz = pytz.timezone('Africa/Cairo')

# --- محرك جوجل شيت ---
def get_sheet_service():
    creds = service_account.Credentials.from_service_account_file(
        'credentials.json', scopes=['https://www.googleapis.com/auth/spreadsheets'])
    return build('sheets', 'v4', credentials=creds).spreadsheets()

# --- دالة تهيئة الشيت (التحكم الكامل) ---
def setup_sheets():
    service = get_sheet_service()
    meta = service.get(spreadsheetId=SHEET_ID).execute()
    existing = [s['properties']['title'] for s in meta['sheets']]
    
    required = {
        "Tasks": [["المهمة", "الحالة", "التاريخ"]],
        "Expenses": [["التاريخ", "المبلغ", "البند"]],
        "Diet": [["اليوم", "الوجبة", "السعرات"]],
        "Gym": [["العضلة", "التمرين", "الوزن"]]
    }
    
    for name, headers in required.items():
        if name not in existing:
            service.batchUpdate(spreadsheetId=SHEET_ID, body={'requests': [{'addSheet': {'properties': {'title': name}}}]}).execute()
        service.values().update(spreadsheetId=SHEET_ID, range=f'{name}!A1:C1', valueInputOption='RAW', body={'values': headers}).execute()
    return "✅ تم ضبط الشيت بالكامل!"

# --- القوائم ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("1️⃣ المهام", callback_data='m1'), InlineKeyboardButton("2️⃣ المصاريف", callback_data='m2')],
        [InlineKeyboardButton("7️⃣ الدايت", callback_data='m7'), InlineKeyboardButton("8️⃣ الجيم", callback_data='m8')],
        [InlineKeyboardButton("🛠️ تهيئة الشيت", callback_data='setup')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "👔 سكرتير محمود المصري جاهز.\nاختار القسم:"
    if update.message: await update.message.reply_text(text, reply_markup=reply_markup)
    else: await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'setup':
        res = setup_sheets()
        await query.edit_message_text(res, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data='home')]]))
    
    elif query.data == 'm1': # مثال لقائمة المهام الفرعية
        keyboard = [
            [InlineKeyboardButton("1.1 إضافة مهمة", callback_data='add_t')],
            [InlineKeyboardButton("🔙 رجوع", callback_data='home')]
        ]
        await query.edit_message_text("📋 قسم المهام:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data == 'home':
        await start(update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    print("🚀 البوت شغال يا حودة.. جرب دلوقتي.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
