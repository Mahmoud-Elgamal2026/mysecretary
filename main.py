import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- الإعدادات ---
TOKEN = "8569606909:AAEdLS1E5aruUZW60EPDThrWyGIsCUQlBNs"
SHEET_ID = "18uJrVBBjOOg51sReKhXdxmZdWnBsuAhZlEBda6K8JG8"

# دالة البحث عن ملف الصلاحيات الذكي
def get_sheet_service():
    # بنجرب الأسماء اللي ظاهرة في صورتك يا حودة
    possible_files = ['credentials.json', 'creds.json', 'client_secret_784859042228-a7l7m6i9rc22041...json']
    
    auth_file = None
    for f in possible_files:
        if os.path.exists(f):
            auth_file = f
            break
            
    if not auth_file:
        raise FileNotFoundError("يا حودة مفيش ملف JSON شغال في الفولدر.. تأكد من الاسم!")
    
    print(f"✅ تم استخدام ملف: {auth_file}")
    creds = service_account.Credentials.from_service_account_file(
        auth_file, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    return build('sheets', 'v4', credentials=creds, cache_discovery=False).spreadsheets()

def setup_all_sheets_sync():
    try:
        service = get_sheet_service()
        # بقية الكود لإنشاء التابات
        required = {
            "Tasks": [["المهمة", "الحالة", "التاريخ"]],
            "Expenses": [["التاريخ", "المبلغ", "البند"]],
            "YouTube": [["التاريخ", "الفكرة", "المشتركين"]],
            "Appointments": [["المناسبة", "التاريخ", "التذكير"]],
            "Diet": [["اليوم", "الوجبة", "السعرات"]],
            "Gym": [["العضلة", "التمرين", "الوزن"]],
            "Emails": [["التاريخ", "المرسل", "الملخص"]]
        }
        
        meta = service.get(spreadsheetId=SHEET_ID).execute()
        existing = [s['properties']['title'] for s in meta['sheets']]
        
        for name, headers in required.items():
            if name not in existing:
                service.batchUpdate(spreadsheetId=SHEET_ID, body={'requests': [{'addSheet': {'properties': {'title': name}}}]}).execute()
            service.values().update(spreadsheetId=SHEET_ID, range=f'{name}!A1:C1', valueInputOption='RAW', body={'values': headers}).execute()
        return "✅ مبروك يا حودة! الشيت اتملى تابات دلوقتي."
    except Exception as e:
        return f"❌ خطأ: {str(e)}"

# --- القوائم ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("1️⃣ المهام", callback_data='lv1_1'), InlineKeyboardButton("2️⃣ المصاريف", callback_data='lv1_2')],
        [InlineKeyboardButton("7️⃣ الدايت", callback_data='lv1_7'), InlineKeyboardButton("8️⃣ الجيم", callback_data='lv1_8')],
        [InlineKeyboardButton("🛠️ تهيئة الشيت", callback_data='setup')]
    ]
    if update.message: await update.message.reply_text("👔 جاهز يا حودة.. اختار:", reply_markup=InlineKeyboardMarkup(keyboard))
    else: await update.callback_query.edit_message_text("👔 جاهز يا حودة.. اختار:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'setup':
        await query.edit_message_text("⏳ ثواني بفتح الشيت...")
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(None, setup_all_sheets_sync)
        await query.edit_message_text(res, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data='home')]]))
    elif query.data == 'home': await start(update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
