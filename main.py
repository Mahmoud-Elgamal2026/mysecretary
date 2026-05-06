from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = "8569606909:AAEdLS1E5aruUZW60EPDThrWyGIsCUQlBNs"

# --- 1. القائمة الرئيسية الشاملة ---
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("1️⃣ المهام", callback_data='m1'), InlineKeyboardButton("2️⃣ المصاريف", callback_data='m2')],
        [InlineKeyboardButton("3️⃣ يوتيوب", callback_data='m3'), InlineKeyboardButton("4️⃣ المواعيد", callback_data='m4')],
        [InlineKeyboardButton("5️⃣ الترجمة", callback_data='m5'), InlineKeyboardButton("6️⃣ الإيميلات", callback_data='m6')],
        [InlineKeyboardButton("7️⃣ البرنامج الغذائي 🍎", callback_data='m7'), InlineKeyboardButton("8️⃣ تمرين الجيم 🏋️", callback_data='m8')]
    ]
    text = "👔 سكرتير ومساعد محمود الشخصي.\nجاهز لتنفيذ أوامرك، اختار القسم:"
    
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# --- 2. معالج القوائم الفرعية والرجوع ---
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # تعريف كافة القوائم الفرعية
    menus = {
        'm1': ("🛠️ إدارة المهام", [("1.1 إضافة مهمة", "11"), ("1.2 عرض الكل", "12"), ("1.3 حذف مهمة", "13")]),
        'm2': ("💰 المصاريف", [("2.1 تسجيل مصروف", "21"), ("2.2 تقرير الشهر", "22")]),
        'm3': ("🎥 إدارة اليوتيوب", [("3.1 إحصائيات", "31"), ("3.2 أفكار فيديوهات", "32")]),
        'm4': ("🗓️ المواعيد", [("4.1 إضافة موعد", "41"), ("4.2 تذكير بمناسبة", "42")]),
        'm5': ("🔤 المترجم الفوري", [("5.1 ترجمة نص", "51"), ("5.2 ترجمة صوت", "52")]),
        'm6': ("📧 الإيميلات", [("6.1 ملخص البريد", "61"), ("6.2 مسودة سريع", "62")]),
        'm7': ("🍎 البرنامج الغذائي", [("7.1 وجبات اليوم", "71"), ("7.2 حساب السعرات", "72"), ("7.3 نصائح تغذية", "73")]),
        'm8': ("🏋️ برنامج الجيم", [("8.1 جدول التمرين", "81"), ("8.2 تسجيل الوزن", "82"), ("8.3 شرح تمارين", "83")])
    }

    if query.data in menus:
        title, options = menus[query.data]
        keyboard = [[InlineKeyboardButton(opt[0], callback_data=opt[1])] for opt in options]
        keyboard.append([InlineKeyboardButton("0️⃣ 🔙 رجوع للقائمة الرئيسية", callback_data='main')])
        await query.edit_message_text(f"{title}:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data == 'main':
        await show_main_menu(update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, show_main_menu))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    print("🚀 سكرتيرك الشخصي والرياضي جاهز يا محمود!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
