import os
import asyncio
import requests
import json
from datetime import datetime
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- الإعدادات الأساسية ---
TOKEN = "8569606909:AAEdLS1E5aruUZW60EPDThrWyGIsCUQlBNs"
SHEET_ID = "18uJrVBBjOOg51sReKhXdxmZdWnBsuAhZlEBda6K8JG8"
WEATHER_API_KEY = "eb1545625c9b4e33967132442240605"
egypt_tz = pytz.timezone('Africa/Cairo')

# بيانات الدخول المحدثة لضمان صلاحيات الإرسال
SERVICE_ACCOUNT_INFO = {
  "type": "service_account",
  "project_id": "my-smart-secretary-495208",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDN9kZ+ZRKSU1s4\n9slCDPkjEl/dgqDblFlcF90qceCX4iQbAq7YNQvvyQaaLKUJz8Wb4miTlrtBfE5D\n6pFt3UIQ06pVSMdCKwhCPnKktNy14XjLIantAL2GdYBe7e75CGvVIlfe8UzwlpyY\n/dPVdOu1u3QyrB48E5JJUB9DJvrQSRT9seSDLo2wqPv59+EjE9wCpbHXEX5rA5Mi\nLf/sswT0AJ2hnxaZ0H2wcDmSu1DTCIwkTKaKquKUiMPlwxW6zdKlgmtsmkYAkSyT\niWrn093sONHS79kr66EgAUKuupXeT85xSsWCio9Qfjfn0muk3Ust+o2wTcf6nhNp\nCH0m8NoTAgMBAAECggEACpkh9tO5SUGez7yV40ngRrdlqslTq6444ZicxIKy8uiB\nFnQPOTLpl/95Jn/Q8kNNwNVoBN2HFI89Rm4Qk7MEo5xbXHjFQBi6G7vePFl42KcZ\n3Hdb/hpr+4+aTnLh5CX/HoAzk1ZJW5afHO7wHUDJ9u0GxVYUAYq5m/99Iask0Yje\n2/5UtsfjkCLNtCRsPSm6+gCEdf3SQ8v6OHKhf4gnywIOArV2WC+phbn5mhdlJ0dk\nXUgwiHdVTibDq0e/rS/aTFY3IiTlKoodgNB1bQYTZ7LkCmx/SMC+Z1eQYXBr0QjD\nB4lPbH4Sy7CatzGC5QUrELihwj8dfyf2lgW+LMSAkQKBgQDxcBX4GlpkVWzhtV89\nWL7xFv+BabiSsvPUN2m4Jz6b/F+AnCd/gIVm++Jf2dH+5nq52/RSV5Gido4O8rY5\nYz7rtHu4UAPliAO3Ta6Q0ceP3UWozzMDj3AOaGvHhzfIIZ6Yt0GWcCjzdhbGxMVe\nr6POIrgIBnO1SS451HO2DfPriwKBgQDaYm0VMOL2q7LkOQxM7ZUaaThvpftAXUci\ngaPev2H9SV9lycO5yrlcL4tLj0lhaNSzFQ//vGH3TmFnY7JtfYZJiV4WzqYrEmeM\nrzK22golltW56AoihCna06x6ZR2k9pGtI4CSJtb4z//EJjJeBEaQaO7HvcaO0ExR\nROY9z228mQKBgCJ+Q/U9NprNBZA9jEzEaAsjoP9JLmBvBpzUCduQZ8Z7SN2j8ZSq\ntORgqhfNk83Z+cCh5wb4kcrnKyaBkH0ka7HbCC3t6JCbXQSMKZtxDRTFpRUX/Q7O\nKFE2o+dOry59dx4UWF94yLD3twtQw23ipAFoPmiPG2rT+LG0Y4+n8Kg/AoGBALSF\nNCKWPKcnG0NonPBiXCRu4gX4sI5uDMVLYMhab4fORRuBA1frafn4Gy8kjMYGv/wg\n5w7BDEI/+mhakz3Ky1yyPqKfw+BK4Gn80PExn72ex6FbXDVYBrkqzKKIP08Duzvh\n4v/tNzqJxaTA5lWtNx9cfjWCfEXFjbCIQcLKWq3RAoGBAKS4+ilremxrEECS3NgR\n0etkcyNx9Gapzjr2jzSBsU/g3QqZ2PqXt5jgjqMdvJizPC1rPIStlogwN2I+9pRr\nrf+p3i29eOvgNdQTnN5suGoIW2FBfePNo15LXuBiH0x7s0WB3FbomgRIHmW6edGa\nwxObjZ5SJLTsBDim6hobvkzn\n-----END PRIVATE KEY-----\n",
  "client_email": "secretary@my-smart-secretary-495208.iam.gserviceaccount.com",
  "token_uri": "https://oauth2.googleapis.com/token"
}

def get_weather():
    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q=Cairo&aqi=no"
        data = requests.get(url).json()
        return f"{data['current']['temp_c']}°C - {data['current']['condition']['text']}"
    except: return "28°C - مشمس وصافٍ"

async def show_main_menu(update: Update):
    now = datetime.now(egypt_tz)
    # تنسيق التاريخ والوقت والطقس المطلوب
    header = "👔 السكرتير الشخصي\n\nأهلاً بك يا محمود، أتمنى لك يوماً سعيداً.\n"
    date_line = f"📅 التاريخ: {now.strftime('%A، %d %B %Y')} م | 🌙 19 ذو القعدة 1447 هـ.\n"
    time_line = f"⌚ الوقت الآن: {now.strftime('%I:%M %p')} بتوقيت القاهرة.\n"
    weather_line = f"🌡️ حالة الطقس: درجة الحرارة {get_weather()}.\n\n"
    perms_line = "🔐 صلاحيات الوصول والأقسام المتاحة\nيرجى اختيار رقم القسم الذي تود التسجيل فيه الآن:"

    keyboard = [
        [InlineKeyboardButton("1️⃣ المهام", callback_data='set_Tasks'), InlineKeyboardButton("2️⃣ المصاريف", callback_data='set_Expenses')],
        [InlineKeyboardButton("3️⃣ يوتيوب", callback_data='set_YouTube'), InlineKeyboardButton("4️⃣ المواعيد", callback_data='set_Appointments')],
        [InlineKeyboardButton("5️⃣ الجيم", callback_data='set_Gym'), InlineKeyboardButton("6️⃣ الدايت", callback_data='set_Diet')],
        [InlineKeyboardButton("7️⃣ الصيانة", callback_data='set_Claims')]
    ]

    text = header + date_line + time_line + weather_line + perms_line
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tab = query.data.split('_')[1]
    context.user_data['current_tab'] = tab
    await query.edit_message_text(f"✅ تم تفعيل القسم رقم ({tab})\nابعت البيانات دلوقتى وهسجلها في تابة {tab} فوراً.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tab = context.user_data.get('current_tab')
    if not tab:
        await show_main_menu(update)
        return

    # تنفيذ قواعد الإرسال الخاصة بمحمود
    info = SERVICE_ACCOUNT_INFO.copy()
    info['private_key'] = info['private_key'].replace('\\n', '\n')
    creds = service_account.Credentials.from_service_account_info(info, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    service = build('sheets', 'v4', credentials=creds).spreadsheets()
    
    now_str = datetime.now(egypt_tz).strftime('%d/%m/%Y %H:%M')
    # الصف المنسق: البيانات، الأولوية، الحالة، التاريخ...
    row = [update.message.text, "عالية", "قيد التنفيذ", now_str, "", "", "", "", "أضيفت عبر السكرتير"]
    
    try:
        service.values().append(spreadsheetId=SHEET_ID, range=f"{tab}!A2", valueInputOption="RAW", body={"values": [row]}).execute()
        await update.message.reply_text(f"✅ تم التسجيل في {tab} بنجاح يا حودة.")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {str(e)}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.COMMAND, start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__": main()
