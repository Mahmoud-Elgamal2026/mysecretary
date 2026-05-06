import os
import asyncio
from datetime import datetime
import pytz
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- الإعدادات الأساسية ---
TOKEN = "8569606909:AAEdLS1E5aruUZW60EPDThrWyGIsCUQlBNs"
SHEET_ID = "18uJrVBBjOOg51sReKhXdxmZdWnBsuAhZlEBda6K8JG8"
egypt_tz = pytz.timezone('Africa/Cairo')

# المفتاح السري بتنسيق سليم تماماً
RAW_KEY = (
    "-----BEGIN PRIVATE KEY-----\n"
    "MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQC9oOxJ6hrRvox9\n"
    "ZWQUKWPNrVTLUYYUEAJPjPBMPafcpjlbIDmyRB/jw8q7Mprxzbbv6JoIoQDT2YoZ\n"
    "SLXa+PZA/8YsPlPPS61QStFjwrfZ/fzX0K9MQl07UyZuueYZNZmQ48N7f+0CyS79\n"
    "E6ugIhtB5C9rRrV90CBc//J/uaAZY4jWe3Cy55YKXlZK2SPJ+j108SyLWd6g5k4B\n"
    "99lNeU5ty/BnfQg70+lpz4JP5jAes8FtPJaFoULhBhiVQjHNsJKZte9BWfgJuiPI\n"
    "N/weYOYvb+eHHFxZXxyu6JJA4NaMUzG2hcM0D5j8dIrfi+bbJvZ7xB65gja+1jgj\n"
    "zc/23tsTAgMBAAECggEAAaoJCzi5I6N63T7+LadU/0qqMBE0/3GsOdETgLhMp3H3\n"
    "KYOgBoNOpmzOmjGoo9c9wbE6luJD84Tzj17iYfLU0vEwedNUt5U4N/GXITXzcl3i\n"
    "PWKX4qfcyUijWafd8UeyIg65ES78pPz8pw/VRTJzWG1oFKmb2XL0gNHjSPh24AJ9\n"
    "4nt8eVcEXBEq+RKNBeDPpehlyycVwBkCSYGFZVuwkpg6ifQgJbm2YWTFgxIzzIe3\n"
    "zHyq8ayP1tEv8WcPLvZIsu+QpQDic9t1qBk7P2MpwnnzpOdlzzaAG9L1OcbnS9pM\n"
    "haXizlXfkmqQtwsxUGyWp+k5jTRiAwBymHXHcuMyaQKBgQDkU85BFEiPK4saLRA+\n"
    "6nlsFXY6184yLjwMUPM1nD9OIfhMlRp5Zc7WEgT3fnoWGhLAgwmKClnflYzS3g7o\n"
    "JzpM7P/JHgWbfzaeKGud0/jMe38QmOB+95XongmqTPLc+71Kac9TA1xU/TUp4ISV\n"
    "0i5UFwztcX7IDC9OY3sn9RdeOQKBgQDUnG5X0ScfXrYKKeGzeIdBW9LJ+cN1Kl5h\n"
    "qRxZTT2+heQYqIegUpI6NBx9sj797jXfp5efkfxIxCJt9hvsslVCQe/tldkGFdCt\n"
    "klC9E29GW8jNoQKn38eyUZQc5lM79/YSNC3A23coWR1I9In45HDrvBP/PCOBiHsa\n"
    "kp6GF2pDqwKBgAzZSnoPEiY8ZQ+MCaYAu+SBMK4PBuN8BpUK2STjLgzPjJGCsoKy\n"
    "X/lb+juTOnuT7Ao5VYgXHQef+tTC+kPGMVmy3JIMxnQBrKkpzSSMkSuwp23frIJ4\n"
    "nE8C1bhnrCMTZ4uQeMJLJh8CQMOihtOHiGPjCC80e9X2GZNntb6B5FbBAoGAPw5q\n"
    "F3d7n+0qFleXje/oRXUjTi3aT2ySc2qBcubash/pp3qMRvtWTRbZgFoWHp/AsKV2\n"
    "7aeRaE9rWquMWqYFbVI7A37Wz9w2eNQVSA50iSx9oKbpL7rJ8lQJloylEPsYqwt4\n"
    "qmMssvXDHrkQFpZB+1hboe5HJYrB3/6uL1zQcmMCgYAswR3/8z8l72xSlO+SRJSp\n"
    "+TydUJAZtPDYAUg/c2HBr3laOAV0NMLNPJjo6rI1E+Ykfrez0/7svFnx97WtXZXw\n"
    "HDmIYrlV/ifhhuNoQB4Vn/Ad5cmczFJ3EIyN0amQFBoXwb1MOL0Vip70aDRcTC6M\n"
    "nPZBEpHHxRRgg8I40f1BnUA==\n"
    "-----END PRIVATE KEY-----"
)

# بيانات الـ Service Account
SERVICE_ACCOUNT_INFO = {
    "type": "service_account",
    "project_id": "my-smart-secretary-495208",
    "private_key": RAW_KEY,
    "client_email": "secretary@my-smart-secretary-495208.iam.gserviceaccount.com",
    "token_uri": "https://oauth2.googleapis.com/token",
}

def get_sheet_service():
    # هنا بنستخدم الـ info مباشرة لضمان عدم حدوث أخطاء ملفات
    creds = service_account.Credentials.from_service_account_info(
        SERVICE_ACCOUNT_INFO, 
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
        return "✅ زي الفل يا محمود، المهمة نزلت في الشيت!"
    except Exception as e:
        return f"❌ حصلت مشكلة تقنية: {str(e)}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    # تجاهل الأوامر لو بعت /start مرتين
    if user_text.startswith('/'): return 
    
    status = await update.message.reply_text("⏳ جاري التسجيل...")
    res = add_task_to_sheet(user_text)
    await status.edit_text(res)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🚀 سكرتير محمود المصري شغال...")
    app.run_polling()

if __name__ == "__main__":
    main()
