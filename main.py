import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- الإعدادات الأساسية ---
TOKEN = "8569606909:AAEdLS1E5aruUZW60EPDThrWyGIsCUQlBNs"
SHEET_ID = "18uJrVBBjOOg51sReKhXdxmZdWnBsuAhZlEBda6K8JG8"

# دالة الربط مع جوجل شيت من السيرفر
def get_sheet_service():
    # بيبحث عن ملف credentials.json اللي إنت رفعته
    auth_file = 'credentials.json'
    if not os.path.exists(auth_file):
        raise FileNotFoundError("السيرفر مش لاقي ملف credentials.json!")
    
    creds = service_account.Credentials.from_service_account_file(
        auth_file, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    return build('sheets', 'v4', credentials=creds, cache_discovery=False).spreadsheets()

def setup_all_sheets_sync():
    try:
        service = get_sheet_service()
        # الـ 8 أقسام اللي اتفقنا عليهم يا حودة
        required = {
            "Tasks": [["المهمة", "الحالة", "التاريخ"]],
            "Expenses": [["التاريخ", "المبلغ", "البند"]],
            "YouTube": [["التاريخ", "فكرة الفيديو", "الحالة"]],
            "Appointments": [["المناسبة", "التاريخ", "التذكير"]],
            "Translation": [["النص الأصلي", "الترجمة", "اللغة"]],
            "Emails": [["التاريخ", "المرسل", "الملخص"]],
            "Diet": [["اليوم", "الوجبة", "السعرات"]],
            "Gym": [["العضلة", "التمرين", "الوزن"]]
        }
        
        meta = service.get(spreadsheetId=SHEET_ID).execute()
        existing = [s['properties']['title'] for s in meta['sheets']]
        
        for name, headers in required.items():
            if name not in existing:
                service.batchUpdate(spreadsheetId=SHEET_ID, body={'requests': [{'addSheet': {'properties': {'title': name}}}]}).execute()
            service.values().update(spreadsheetId=SHEET_ID, range=f'{name}!A1:C1', valueInputOption='RAW', body={'values': headers}).execute()
        return "✅ مبروك يا حودة! الـ 8 أقسام ظهروا في الشيت دلوقتي."
    except Exception as e:
        return f"❌ خطأ: {str(e)}"

# --- القوائم الرئيسية (1-8) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("1️⃣ المهام", callback_data='lv1_1'), InlineKeyboardButton("2️⃣ المصاريف", callback_data='lv1_2')],
        [InlineKeyboardButton("3️⃣ يوتيوب 🎥", callback_data='lv1_3'), InlineKeyboardButton("4️⃣ المواعيد", callback_data='lv1_4')],
        [InlineKeyboardButton("5️⃣ الترجمة", callback_data='lv1_5'), InlineKeyboardButton("6️⃣ الإيميلات", callback_data='lv1_6')],
        [InlineKeyboardButton("7️⃣ الدايت 🍎", callback_data='lv1_7'), InlineKeyboardButton("8️⃣ الجيم 🏋️", callback_data='lv1_8')],
        [InlineKeyboardButton("🛠️ تهيئة الشيت بالكامل", callback_data='setup')]
    ]
    text = "👔 سكرتير محمود المصري جاهز.\nاختار القسم المطلوب:"
    if update.message: await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else: await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'setup':
        await query.edit_message_text("⏳ جاري تهيئة الـ 8 أقسام في الشيت...")
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(None, setup_all_sheets_sync)
        await query.edit_message_text(res, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data='home')]]))
    
    elif query.data.startswith('lv1_'):
        code = query.data.split('_')[1]
        sections = {"1":"المهام", "2":"المصاريف", "3":"يوتيوب", "4":"المواعيد", "5":"الترجمة", "6":"الإيميلات", "7":"الدايت", "8":"الجيم"}
        await query.edit_message_text(f"📂 قسم [{sections[code]}] جاهز يا محمود.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data='home')]]))
    
    elif query.data == 'home':
        await start(update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
