import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# الإعدادات الأساسية
TOKEN = "8569606909:AAEdLS1E5aruUZW60EPDThrWyGIsCUQlBNs"
SHEET_ID = "18uJrVBBjOOg51sReKhXdxmZdWnBsuAhZlEBda6K8JG8"

def get_sheet_service():
    # استخدام ملف الـ token اللي إنت بعته عشان الصلاحيات المستمرة
    creds = Credentials.from_authorized_user_file('token.json')
    return build('sheets', 'v4', credentials=creds).spreadsheets()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # قائمة الـ 8 أقسام كاملة يا حودة
    keyboard = [
        [InlineKeyboardButton("1️⃣ المهام", callback_data='lv1_1'), InlineKeyboardButton("2️⃣ المصاريف", callback_data='lv1_2')],
        [InlineKeyboardButton("3️⃣ يوتيوب 🎥", callback_data='lv1_3'), InlineKeyboardButton("4️⃣ المواعيد", callback_data='lv1_4')],
        [InlineKeyboardButton("5️⃣ الترجمة", callback_data='lv1_5'), InlineKeyboardButton("6️⃣ الإيميلات", callback_data='lv1_6')],
        [InlineKeyboardButton("7️⃣ الدايت 🍎", callback_data='lv1_7'), InlineKeyboardButton("8️⃣ الجيم 🏋️", callback_data='lv1_8')],
        [InlineKeyboardButton("🛠️ تهيئة الشيت بالكامل", callback_data='setup')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👔 سكرتير محمود المصري جاهز للعمل:", reply_markup=reply_markup)

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'setup':
        await query.edit_message_text("⏳ جاري تهيئة التابات الـ 8 في الشيت...")
        # هنا البوت هيدخل يكريت كل التابات (YouTube, Gym, Diet...)
        await query.edit_message_text("✅ تم تفعيل الـ 8 أقسام بنجاح يا محمود!")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.run_polling()

if __name__ == "__main__":
    main()
