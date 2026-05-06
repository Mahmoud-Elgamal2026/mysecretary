import os
import asyncio
from datetime import datetime
import pytz
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- الإعدادات ---
TOKEN = "8569606909:AAEdLS1E5aruUZW60EPDThrWyGIsCUQlBNs"
SHEET_ID = "18uJrVBBjOOg51sReKhXdxmZdWnBsuAhZlEBda6K8JG8"
egypt_tz = pytz.timezone('Africa/Cairo')

def get_sheet_service():
    # الطريقة دي بتفتح الملف الخام من السيرفر وبتقرأه زي ما هو
    # وده بيمنع أي تلاعب في "السطور الجديدة" أو "التشفير"
    auth_file = 'credentials.json'
    if not os.path.exists(auth_file):
        raise FileNotFoundError("يا محمود السيرفر مش لاقي ملف credentials.json!")
        
    creds = service_account.Credentials.from_service_account_file(
        auth_file, 
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    return build('sheets', 'v4', credentials=creds, cache_discovery=False).spreadsheets()

def add_task_to_sheet(task_name):
    try:
        service = get_sheet_service()
        now_date = datetime.now(egypt_tz).strftime('%d/%m/%Y')
        now_time = datetime.now(egypt_tz).strftime('%H:%M')
        
        # الترتيب حسب شيت محمود الملون: المهمة، الأولوية، الحالة، تاريخ الإضافة...
        row_data = [task_name, "عالية", "قيد التنفيذ", now_date, now_time, "", "", "", "إضافة سريعة"]
        
        service.values().append(
            spreadsheetId=SHEET_ID, 
            range="Tasks!A2",
            valueInputOption="RAW", 
            body={"values": [row_data]}
        ).execute()
        return "✅ أخيراً يا حودة! المهمة نزلت في الشيت."
    except Exception as e:
        return f"❌ خطأ تقني: {str(e)}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if user_text.startswith('/'): return 
    status = await update.message.reply_text("⏳ جاري الإرسال للشيت...")
    res = add_task_to_sheet(user_text)
    await status.edit_text(res)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🚀 البوت انطلق...")
    app.run_polling()

if __name__ == "__main__":
    main()
