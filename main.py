import os
import json
import logging
import asyncio
from datetime import datetime
import pytz
from groq import Groq
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from google.oauth2 import service_account
from googleapiclient.discovery import build
from concurrent.futures import ThreadPoolExecutor

# 1. الإعدادات الأساسية
TOKEN = "8569606909:AAEdLS1E5aruUZW60EPDThrWyGIsCUQlBNs"
GROQ_KEY = "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"
SHEET_ID = "18uJrVBBjOOg51sReKhXdxmZdWnBsuAhZlEBda6K8JG8"
client = Groq(api_key=GROQ_KEY)
executor = ThreadPoolExecutor(max_workers=10)
egypt_tz = pytz.timezone('Africa/Cairo')

# 2. محرك التحكم في جوجل شيت
class SheetController:
    def __init__(self):
        self.path = 'credentials.json'
        self.creds = service_account.Credentials.from_service_account_file(
            self.path, scopes=['https://www.googleapis.com/auth/spreadsheets'])
        self.service = build('sheets', 'v4', credentials=self.creds, cache_discovery=False).spreadsheets()

    def setup_all_sheets(self):
        """تجهيز كافة الصفحات والعناوين تلقائياً"""
        try:
            meta = self.service.get(spreadsheetId=SHEET_ID).execute()
            sheets = [s['properties']['title'] for s in meta['sheets']]
            
            required = {
                "Tasks": [["ID", "المهمة", "الأولوية", "الحالة", "التاريخ"]],
                "Expenses": [["التاريخ", "المبلغ", "البند", "ملاحظات"]],
                "Diet": [["اليوم", "الوجبة", "المكونات", "السعرات"]],
                "Gym": [["العضلة", "التمرين", "المجموعات", "العدات", "الوزن"]]
            }
            
            for name, headers in required.items():
                if name not in sheets:
                    self.service.batchUpdate(spreadsheetId=SHEET_ID, 
                        body={'requests': [{'addSheet': {'properties': {'title': name}}}]}).execute()
                self.service.values().update(spreadsheetId=SHEET_ID, range=f'{name}!A1:E1',
                    valueInputOption='RAW', body={'values': headers}).execute()
            return "✅ الشيت جاهز بنسبة 100%"
        except Exception as e: return f"❌ خطأ إعداد الشيت: {e}"

    def add_data(self, sheet_name, row):
        try:
            self.service.values().append(spreadsheetId=SHEET_ID, range=f'{sheet_name}!A:E',
                valueInputOption='USER_ENTERED', body={'values': [row]}).execute()
            return True
        except: return False

sheet_manager = SheetController()

# 3. نظام القوائم (Levels)
async def start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("1️⃣ المهام", callback_data='lv1_1'), InlineKeyboardButton("2️⃣ المصاريف", callback_data='lv1_2')],
        [InlineKeyboardButton("3️⃣ يوتيوب", callback_data='lv1_3'), InlineKeyboardButton("4️⃣ المواعيد", callback_data='lv1_4')],
        [InlineKeyboardButton("5️⃣ الترجمة", callback_data='lv1_5'), InlineKeyboardButton("6️⃣ الإيميلات", callback_data='lv1_6')],
        [InlineKeyboardButton("7️⃣ الدايت 🍎", callback_data='lv1_7'), InlineKeyboardButton("8️⃣ الجيم 🏋️", callback_data='lv1_8')],
        [InlineKeyboardButton("🛠️ تهيئة الشيت بالكامل", callback_data='setup_sheets')]
    ]
    text = "👔 أهلاً يا محمود (حودة)! أنا سكرتيرك الشخصي.\nاختار القسم اللي عاوزه:"
    if update.message: await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else: await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # منطق القوائم الفرعية
    if query.data.startswith('lv1_'):
        code = query.data.split('_')[1]
        titles = {"1":"المهام", "2":"المصاريف", "3":"يوتيوب", "4":"المواعيد", "5":"الترجمة", "6":"الإيميلات", "7":"الدايت", "8":"الجيم"}
        keyboard = [
            [InlineKeyboardButton(f"{code}.1 إضافة/تسجيل", callback_data=f"act_{code}_add")],
            [InlineKeyboardButton(f"{code}.2 عرض البيانات", callback_data=f"act_{code}_view")],
            [InlineKeyboardButton("0️⃣ 🔙 رجوع", callback_data='main')]
        ]
        await query.edit_message_text(f"📂 قسم {titles[code]}:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'setup_sheets':
        res = sheet_manager.setup_all_sheets()
        await query.edit_message_text(res, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data='main')]]))

    elif query.data == 'main': await start_menu(update, context)

# 4. معالج الرسائل (بدون تهنيج)
async def process_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    # هنا ممكن نربط الذكاء الاصطناعي للرد أو تنفيذ أوامر الأرقام
    await update.message.reply_text(f"وصل يا حودة: {user_text}\n(اختار من القائمة للتحكم في الشيت)")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start_menu))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    
    print("🚀 سكرتير محمود انطلق! كل الصلاحيات والتحكم في الشيت جاهزة.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
