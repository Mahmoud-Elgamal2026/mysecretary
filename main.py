import os
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
egypt_tz = pytz.timezone('Africa/Cairo')

# بيانات الـ Service Account كاملة مع الـ token_uri المفقود
SERVICE_ACCOUNT_INFO = {
  "type": "service_account",
  "project_id": "my-smart-secretary-495208",
  "private_key_id": "ebdb70840b7294fc3e801ad655dbfc842ae375a1",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQC9oOxJ6hrRvox9\nZWQUKWPNrVTLUYYUEAJPjPBMPafcpjlbIDmyRB/jw8q7Mprxzbbv6JoIoQDT2YoZ\nSLXa+PZA/8YsPlPPS61QStFjwrfZ/fzX0K9MQl07UyZuueYZNZmQ48N7f+0CyS79\nE6ugIhtB5C9rRrV90CBc//J/uaAZY4jWe3Cy55YKXlZK2SPJ+j108SyLWd6g5k4B\n99lNeU5ty/BnfQg70+lpz4JP5jAes8FtPJaFoULhBhiVQjHNsJKZte9BWfgJuiPI\nN/weYOYvb+eHHFxZXxyu6JJA4NaMUzG2hcM0D5j8dIrfi+bbJvZ7xB65gja+1jgj\nzc/23tsTAgMBAAECggEAAaoJCzi5I6N63T7+LadU/0qqMBE0/3GsOdETgLhMp3H3\nKYOgBoNOpmzOmjGoo9c9wbE6luJD84Tzj17iYfLU0vEwedNUt5U4N/GXITXzcl3i\nPWKX4qfcyUijWafd8UeyIg65ES78pPz8pw/VRTJzWG1oFKmb2XL0gNHjSPh24AJ9\n4nt8eVcEXBEq+RKNBeDPpehlyycVwBkCSYGFZVuwkpg6ifQgJbm2YWTFgxIzzIe3\nzHyq8ayP1tEv8WcPLvZIsu+QpQDic9t1qBk7P2MpwnnzpOdlzzaAG9L1OcbnS9pM\haXizlXfkmqQtwsxUGyWp+k5jTRiAwBymHXHcuMyaQKBgQDkU85BFEiPK4saLRA+\n6nlsFXY6184yLjwMUPM1nD9OIfhMlRp5Zc7WEgT3fnoWGhLAgwmKClnflYzS3g7o\nJzpM7P/JHgWbfzaeKGud0/jMe38QmOB+95XongmqTPLc+71Kac9TA1xU/TUp4ISV\n0i5UFwztcX7IDC9OY3sn9RdeOQKBgQDUnG5X0ScfXrYKKeGzeIdBW9LJ+cN1Kl5h\nqRxZTT2+heQYqIegUpI6NBx9sj797jXfp5efkfxIxCJt9hvsslVCQe/tldkGFdCt\klC9E29GW8jNoQKn38eyUZQc5lM79/YSNC3A23coWR1I9In45HDrvBP/PCOBiHsa\nkp6GF2pDqwKBgAzZSnoPEiY8ZQ+MCaYAu+SBMK4PBuN8BpUK2STjLgzPjJGCsoKy\nX/lb+juTOnuT7Ao5VYgXHQef+tTC+kPGMVmy3JIMxnQBrKkpzSSMkSuwp23frIJ4\nnE8C1bhnrCMTZ4uQeMJLJh8CQMOihtOHiGPjCC80e9X2GZNntb6B5FbBAoGAPw5q\nF3d7n+0qFleXje/oRXUjTi3aT2ySc2qBcubash/pp3qMRvtWTRbZgFoWHp/AsKV2\n7aeRaE9rWquMWqYFbVI7A37Wz9w2eNQVSA50iSx9oKbpL7rJ8lQJloylEPsYqwt4\nqmMssvXDHrkQFpZB+1hboe5HJYrB3/6uL1zQcmMCgYAswR3/8z8l72xSlO+SRJSp\n+TydUJAZtPDYAUg/c2HBr3laOAV0NMLNPJjo6rI1E+Ykfrez0/7svFnx97WtXZXw\nHDmIYrlV/ifhhuNoQB4Vn/Ad5cmczFJ3EIyN0amQFBoXwb1MOL0Vip70aDRcTC6M\nPZBEpHHxRRgg8I40f1BnUA==\n-----END PRIVATE KEY-----\n",
  "client_email": "secretary@my-smart-secretary-495208.iam.gserviceaccount.com",
  "token_uri": "https://oauth2.googleapis.com/token",
  "universe_domain": "googleapis.com"
}

def get_sheet_service():
    creds = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    return build('sheets', 'v4', credentials=creds, cache_discovery=False).spreadsheets()

def add_task_to_sheet(task_name):
    try:
        service = get_sheet_service()
        now_date = datetime.now(egypt_tz).strftime('%d/%m/%Y')
        now_time = datetime.now(egypt_tz).strftime('%H:%M')
        
        # الترتيب بناءً على صورة الشيت الخاصة بك (Columns A to I)
        row_data = [
            task_name,          # العمود A: المهمة
            "متوسطة",            # العمود B: الأولوية
            "قيد التنفيذ",       # العمود C: الحالة
            now_date,           # العمود D: تاريخ الإضافة
            now_time,           # العمود E: وقت البداية
            "",                 # العمود F: وقت الانتهاء
            "",                 # العمود G: وقت التنفيذ المتوقع
            "",                 # العمود H: الديدلاين
            "تمت الإضافة عبر البوت" # العمود I: ملاحظات
        ]
        
        service.values().append(
            spreadsheetId=SHEET_ID, range="Tasks!A2",
            valueInputOption="RAW", body={"values": [row_data]}
        ).execute()
        return "✅ المهمة نزلت في مكانها الصح يا محمود!"
    except Exception as e:
        return f"❌ خطأ تقني: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👔 سكرتير محمود المصري جاهز.\nابعت لي المهمة اللي عايز تسجلها:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    res = add_task_to_sheet(user_text)
    await update.message.reply_text(res)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
