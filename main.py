import logging
import asyncio
from datetime import datetime
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- الإعدادات ---
TOKEN = "8569606909:AAEdLS1E5aruUZW60EPDThrWyGIsCUQlBNs"
SHEET_ID = "18uJrVBBjOOg51sReKhXdxmZdWnBsuAhZlEBda6K8JG8"

# --- محرك جوجل شيت ---
def get_sheet_service():
    creds = service_account.Credentials.from_service_account_file(
        'credentials.json', scopes=['https://www.googleapis.com/auth/spreadsheets'])
    return build('sheets', 'v4', credentials=creds, cache_discovery=False).spreadsheets()

# دالة التهيئة (تم تعديلها لتكون أسرع)
def setup_all_sheets_sync():
    try:
        service = get_sheet_service()
        meta = service.get(spreadsheetId=SHEET_ID).execute()
        existing = [s['properties']['title'] for s in meta['sheets']]
        
        required = {
            "Tasks": [["المهمة", "الحالة", "التاريخ"]],
            "Expenses": [["التاريخ", "المبلغ", "البند"]],
            "YouTube": [["التاريخ", "الفكرة", "المشتركين"]],
            "Appointments": [["المناسبة", "التاريخ", "التذكير"]],
            "Diet": [["اليوم", "الوجبة", "السعرات"]],
            "Gym": [["العضلة", "التمرين", "الوزن"]],
            "Emails": [["التاريخ", "المرسل", "الملخص"]]
        }
        
        for name, headers in required.items():
            if name not in existing:
                service.batchUpdate(spreadsheetId=SHEET_ID, body={'requests': [{'addSheet': {'properties': {'title': name}}}]}).execute()
            service.values().update(spreadsheetId=SHEET_ID, range=f'{name}!A1:C1', valueInputOption='RAW', body={'values': headers}).execute()
        return "✅ تم تفعيل الـ 7 تابات بنجاح يا حودة!"
    except Exception as e:
        return f"❌ حصل مشكلة: {str(e)}"

# --- القوائم ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("1️⃣ المهام", callback_data='lv1_1'), InlineKeyboardButton("2️⃣ المصاريف", callback_data='lv1_2')],
        [InlineKeyboardButton("3️⃣ يوتيوب", callback_data='lv1_3'), InlineKeyboardButton("4️⃣ المواعيد", callback_data='lv1_4')],
        [InlineKeyboardButton("5️⃣ الترجمة", callback_data='lv1_5'), InlineKeyboardButton("6️⃣ الإيميلات", callback_data='lv1_6')],
        [InlineKeyboardButton("7️⃣ الدايت", callback_data='lv1_7'), InlineKeyboardButton("8️⃣ الجيم", callback_data='lv1_8')],
        [InlineKeyboardButton("🛠️ تهيئة الشيت بالكامل", callback_data='setup')]
    ]
    text = "👔 سكرتير محمود المصري جاهز.\nاختار القسم المطلوب:"
    if update.message: await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else: await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # رد فوري عشان الزرار ميفضلش يلف
    
    if query.data == 'setup':
        await query.edit_message_text("⏳ جاري تهيئة التابات في الشيت.. ثواني يا حودة.")
        # تشغيل العملية في الخلفية عشان البوت ميهنجش
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(None, setup_all_sheets_sync)
        await query.edit_message_text(res, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data='home')]]))
    
    elif query.data.startswith('lv1_'):
        code = query.data.split('_')[1]
        keyboard = [
            [InlineKeyboardButton(f"{code}.1 إضافة/تسجيل", callback_data=f"add_{code}")],
            [InlineKeyboardButton("0️⃣ 🔙 رجوع", callback_data='home')]
        ]
        await query.edit_message_text(f"📂 القسم رقم [{code}]:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data == 'home':
        await start(update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    print("🚀 البوت جاهز للاستخدام يا محمود!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
