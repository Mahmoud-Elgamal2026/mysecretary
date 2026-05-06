import os
import asyncio
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- الإعدادات ---
TOKEN = "8569606909:AAEdLS1E5aruUZW60EPDThrWyGIsCUQlBNs"
SHEET_ID = "18uJrVBBjOOg51sReKhXdxmZdWnBsuAhZlEBda6K8JG8"

# وضعنا البيانات هنا مباشرة لضمان عدم حدوث خطأ في التوقيع (Signature)
SERVICE_ACCOUNT_INFO = {
  "type": "service_account",
  "project_id": "my-smart-secretary-495208",
  "private_key_id": "ebdb70840b7294fc3e801ad655dbfc842ae375a1",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQC9oOxJ6hrRvox9\nZWQUKWPNrVTLUYYUEAJPjPBMPafcpjlbIDmyRB/jw8q7Mprxzbbv6JoIoQDT2YoZ\nSLXa+PZA/8YsPlPPS61QStFjwrfZ/fzX0K9MQl07UyZuueYZNZmQ48N7f+0CyS79\nE6ugIhtB5C9rRrV90CBc//J/uaAZY4jWe3Cy55YKXlZK2SPJ+j108SyLWd6g5k4B\n99lNeU5ty/BnfQg70+lpz4JP5jAes8FtPJaFoULhBhiVQjHNsJKZte9BWfgJuiPI\nN/weYOYvb+eHHFxZXxyu6JJA4NaMUzG2hcM0D5j8dIrfi+bbJvZ7xB65gja+1jgj\nzc/23tsTAgMBAAECggEAAaoJCzi5I6N63T7+LadU/0qqMBE0/3GsOdETgLhMp3H3\nKYOgBoNOpmzOmjGoo9c9wbE6luJD84Tzj17iYfLU0vEwedNUt5U4N/GXITXzcl3i\nPWKX4qfcyUijWafd8UeyIg65ES78pPz8pw/VRTJzWG1oFKmb2XL0gNHjSPh24AJ9\n4nt8eVcEXBEq+RKNBeDPpehlyycVwBkCSYGFZVuwkpg6ifQgJbm2YWTFgxIzzIe3\nzHyq8ayP1tEv8WcPLvZIsu+QpQDic9t1qBk7P2MpwnnzpOdlzzaAG9L1OcbnS9pM\haXizlXfkmqQtwsxUGyWp+k5jTRiAwBymHXHcuMyaQKBgQDkU85BFEiPK4saLRA+\n6nlsFXY6184yLjwMUPM1nD9OIfhMlRp5Zc7WEgT3fnoWGhLAgwmKClnflYzS3g7o\nJzpM7P/JHgWbfzaeKGud0/jMe38QmOB+95XongmqTPLc+71Kac9TA1xU/TUp4ISV\n0i5UFwztcX7IDC9OY3sn9RdeOQKBgQDUnG5X0ScfXrYKKeGzeIdBW9LJ+cN1Kl5h\nqRxZTT2+heQYqIegUpI6NBx9sj797jXfp5efkfxIxCJt9hvsslVCQe/tldkGFdCt\klC9E29GW8jNoQKn38eyUZQc5lM79/YSNC3A23coWR1I9In45HDrvBP/PCOBiHsa\nkp6GF2pDqwKBgAzZSnoPEiY8ZQ+MCaYAu+SBMK4PBuN8BpUK2STjLgzPjJGCsoKy\nX/lb+juTOnuT7Ao5VYgXHQef+tTC+kPGMVmy3JIMxnQBrKkpzSSMkSuwp23frIJ4\nnE8C1bhnrCMTZ4uQeMJLJh8CQMOihtOHiGPjCC80e9X2GZNntb6B5FbBAoGAPw5q\nF3d7n+0qFleXje/oRXUjTi3aT2ySc2qBcubash/pp3qMRvtWTRbZgFoWHp/AsKV2\n7aeRaE9rWquMWqYFbVI7A37Wz9w2eNQVSA50iSx9oKbpL7rJ8lQJloylEPsYqwt4\nqmMssvXDHrkQFpZB+1hboe5HJYrB3/6uL1zQcmMCgYAswR3/8z8l72xSlO+SRJSp\n+TydUJAZtPDYAUg/c2HBr3laOAV0NMLNPJjo6rI1E+Ykfrez0/7svFnx97WtXZXw\nHDmIYrlV/ifhhuNoQB4Vn/Ad5cmczFJ3EIyN0amQFBoXwb1MOL0Vip70aDRcTC6M\nPZBEpHHxRRgg8I40f1BnUA==\n-----END PRIVATE KEY-----\n",
  "client_email": "secretary@my-smart-secretary-495208.iam.gserviceaccount.com",
  "client_id": "107184973306692189636",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/secretary%40my-smart-secretary-495208.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

def get_sheet_service():
    creds = service_account.Credentials.from_service_account_info(
        SERVICE_ACCOUNT_INFO, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    return build('sheets', 'v4', credentials=creds, cache_discovery=False).spreadsheets()

def setup_all_sheets_sync():
    try:
        service = get_sheet_service()
        # الأقسام الثمانية المطلوبة
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
        return "✅ مبروك يا حودة! الـ 8 أقسام اشتغلوا في الشيت."
    except Exception as e:
        return f"❌ خطأ: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("1️⃣ المهام", callback_data='lv1_1'), InlineKeyboardButton("2️⃣ المصاريف", callback_data='lv1_2')],
        [InlineKeyboardButton("3️⃣ يوتيوب 🎥", callback_data='lv1_3'), InlineKeyboardButton("4️⃣ المواعيد", callback_data='lv1_4')],
        [InlineKeyboardButton("5️⃣ الترجمة", callback_data='lv1_5'), InlineKeyboardButton("6️⃣ الإيميلات", callback_data='lv1_6')],
        [InlineKeyboardButton("7️⃣ الدايت 🍎", callback_data='lv1_7'), InlineKeyboardButton("8️⃣ الجيم 🏋️", callback_data='lv1_8')],
        [InlineKeyboardButton("🛠️ تهيئة الشيت بالكامل", callback_data='setup')]
    ]
    if update.message: await update.message.reply_text("👔 سكرتير محمود المصري جاهز:", reply_markup=InlineKeyboardMarkup(keyboard))
    else: await update.callback_query.edit_message_text("👔 سكرتير محمود المصري جاهز:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'setup':
        await query.edit_message_text("⏳ جاري تهيئة التابات الـ 8 في الإكسيل...")
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
