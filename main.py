import os
import asyncio
import json
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

SERVICE_ACCOUNT_INFO = {
  "type": "service_account",
  "project_id": "my-smart-secretary-495208",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDN9kZ+ZRKSU1s4\n9slCDPkjEl/dgqDblFlcF90qceCX4iQbAq7YNQvvyQaaLKUJz8Wb4miTlrtBfE5D\n6pFt3UIQ06pVSMdCKwhCPnKktNy14XjLIantAL2GdYBe7e75CGvVIlfe8UzwlpyY\n/dPVdOu1u3QyrB48E5JJUB9DJvrQSRT9seSDLo2wqPv59+EjE9wCpbHXEX5rA5Mi\nLf/sswT0AJ2hnxaZ0H2wcDmSu1DTCIwkTKaKquKUiMPlwxW6zdKlgmtsmkYAkSyT\niWrn093sONHS79kr66EgAUKuupXeT85xSsWCio9Qfjfn0muk3Ust+o2wTcf6nhNp\nCH0m8NoTAgMBAAECggEACpkh9tO5SUGez7yV40ngRrdlqslTq6444ZicxIKy8uiB\nFnQPOTLpl/95Jn/Q8kNNwNVoBN2HFI89Rm4Qk7MEo5xbXHjFQBi6G7vePFl42KcZ\n3Hdb/hpr+4+aTnLh5CX/HoAzk1ZJW5afHO7wHUDJ9u0GxVYUAYq5m/99Iask0Yje\n2/5UtsfjkCLNtCRsPSm6+gCEdf3SQ8v6OHKhf4gnywIOArV2WC+phbn5mhdlJ0dk\nXUgwiHdVTibDq0e/rS/aTFY3IiTlKoodgNB1bQYTZ7LkCmx/SMC+Z1eQYXBr0QjD\nB4lPbH4Sy7CatzGC5QUrELihwj8dfyf2lgW+LMSAkQKBgQDxcBX4GlpkVWzhtV89\nWL7xFv+BabiSsvPUN2m4Jz6b/F+AnCd/gIVm++Jf2dH+5nq52/RSV5Gido4O8rY5\nYz7rtHu4UAPliAO3Ta6Q0ceP3UWozzMDj3AOaGvHhzfIIZ6Yt0GWcCjzdhbGxMVe\nr6POIrgIBnO1SS451HO2DfPriwKBgQDaYm0VMOL2q7LkOQxM7ZUaaThvpftAXUci\ngaPev2H9SV9lycO5yrlcL4tLj0lhaNSzFQ//vGH3TmFnY7JtfYZJiV4WzqYrEmeM\nrzK22golltW56AoihCna06x6ZR2k9pGtI4CSJtb4z//EJjJeBEaQaO7HvcaO0ExR\nROY9z228mQKBgCJ+Q/U9NprNBZA9jEzEaAsjoP9JLmBvBpzUCduQZ8Z7SN2j8ZSq\ntORgqhfNk83Z+cCh5wb4kcrnKyaBkH0ka7HbCC3t6JCbXQSMKZtxDRTFpRUX/Q7O\nKFE2o+dOry59dx4UWF94yLD3twtQw23ipAFoPmiPG2rT+LG0Y4+n8Kg/AoGBALSF\nNCKWPKcnG0NonPBiXCRu4gX4sI5uDMVLYMhab4fORRuBA1frafn4Gy8kjMYGv/wg\n5w7BDEI/+mhakz3Ky1yyPqKfw+BK4Gn80PExn72ex6FbXDVYBrkqzKKIP08Duzvh\n4v/tNzqJxaTA5lWtNx9cfjWCfEXFjbCIQcLKWq3RAoGBAKS4+ilremxrEECS3NgR\n0etkcyNx9Gapzjr2jzSBsU/g3QqZ2PqXt5jgjqMdvJizPC1rPIStlogwN2I+9pRr\nrf+p3i29eOvgNdQTnN5suGoIW2FBfePNo15LXuBiH0x7s0WB3FbomgRIHmW6edGa\nwxObjZ5SJLTsBDim6hobvkzn\n-----END PRIVATE KEY-----\n",
  "client_email": "secretary@my-smart-secretary-495208.iam.gserviceaccount.com",
  "token_uri": "https://oauth2.googleapis.com/token"
}

def get_sheet_service():
    info = SERVICE_ACCOUNT_INFO.copy()
    info['private_key'] = info['private_key'].replace('\\n', '\n')
    creds = service_account.Credentials.from_service_account_info(info, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    return build('sheets', 'v4', credentials=creds, cache_discovery=False).spreadsheets()

# دالة لإنشاء الـ 8 صفحات تلقائياً
def setup_tabs():
    try:
        service = get_sheet_service()
        tabs = ["Tasks", "Expenses", "YouTube", "Appointments", "Translation", "Emails", "Diet", "Gym"]
        spreadsheet = service.get(spreadsheetId=SHEET_ID).execute()
        existing_tabs = [s['properties']['title'] for s in spreadsheet['sheets']]
        
        requests = []
        for tab in tabs:
            if tab not in existing_tabs:
                requests.append({'addSheet': {'properties': {'title': tab}}})
        
        if requests:
            service.batchUpdate(spreadsheetId=SHEET_ID, body={'requests': requests}).execute()
        return "✅ تم إنشاء جميع الصفحات (التابات) بنجاح يا محمود!"
    except Exception as e: return f"❌ خطأ: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📝 المهام", callback_data='tab_Tasks'), InlineKeyboardButton("💰 المصاريف", callback_data='tab_Expenses')],
        [InlineKeyboardButton("🎥 يوتيوب", callback_data='tab_YouTube'), InlineKeyboardButton("📅 المواعيد", callback_data='tab_Appointments')],
        [InlineKeyboardButton("🍎 دايت", callback_data='tab_Diet'), InlineKeyboardButton("🏋️ جيم", callback_data='tab_Gym')],
        [InlineKeyboardButton("🛠️ تهيئة الصفحات بالكامل", callback_data='setup_all')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👔 سكرتير محمود المصري جاهز للعمل.\nإختار القسم اللي عايز تتعامل معاه أو إضغط تهيئة لإنشاء الصفحات:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'setup_all':
        await query.edit_message_text("⏳ جاري إنشاء الصفحات في الإكسيل...")
        res = setup_tabs()
        await query.edit_message_text(res)
    elif query.data.startswith('tab_'):
        tab_name = query.data.split('_')[1]
        context.user_data['current_tab'] = tab_name
        await query.edit_message_text(f"✅ إنت دلوقتي في قسم: {tab_name}\nأي رسالة هتبعتها هتتسجل هنا.")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tab = context.user_data.get('current_tab', 'Tasks') # الافتراضي هو المهام
    user_text = update.message.text
    
    service = get_sheet_service()
    now = datetime.now(egypt_tz).strftime('%d/%m/%Y %H:%M')
    row = [user_text, "عالية", "قيد التنفيذ", now, "", "", "", "", "أضيفت عبر البوت"]
    
    service.values().append(
        spreadsheetId=SHEET_ID, range=f"{tab}!A2",
        valueInputOption="RAW", body={"values": [row]}
    ).execute()
    await update.message.reply_text(f"✅ تم إضافة السجل في صفحة {tab}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.COMMAND, start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.run_polling()

if __name__ == "__main__": main()
