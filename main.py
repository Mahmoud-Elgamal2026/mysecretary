from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = "8569606909:AAEdLS1E5aruUZW60EPDThrWyGIsCUQlBNs"

# --- القائمة الرئيسية ---
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("1️⃣ المهام", callback_data='m1'), InlineKeyboardButton("2️⃣ المصاريف", callback_data='m2')],
        [InlineKeyboardButton("3️⃣ يوتيوب", callback_data='m3'), InlineKeyboardButton("4️⃣ المواعيد", callback_data='m4')],
        [InlineKeyboardButton("5️⃣ الترجمة", callback_data='m5'), InlineKeyboardButton("6️⃣ الإيميلات", callback_data='m6')]
    ]
    text = "👔 سكرتير محمود الشخصي جاهز.\nاختار الصلاحية المطلوبة:"
    if update.message: await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else: await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# --- معالج الحركات ---
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # توزيع القوائم الفرعية بناءً على الرقم المختار
    menus = {
        'm1': ("🛠️ إدارة المهام", [("1.1 إضافة", "11"), ("1.2 عرض", "12"), ("1.3 حذف", "13")]),
        'm2': ("💰 المصاريف", [("2.1 تسجيل", "21"), ("2.2 تقرير", "22")]),
        'm3': ("🎥 يوتيوب", [("3.1 إحصائيات", "31"), ("3.2 أفكار", "32")]),
        'm4': ("🗓️ المواعيد", [("4.1 إضافة موعد", "41"), ("4.2 تذكير", "42")]),
        'm5': ("🔤 الترجمة", [("5.1 ترجمة نص", "51")]),
        'm6': ("📧 الإيميلات", [("6.1 ملخص", "61"), ("6.2 كتابة", "62")])
    }

    if query.data in menus:
        title, options = menus[query.data]
        keyboard = [[InlineKeyboardButton(opt[0], callback_data=opt[1])] for opt in options]
        keyboard.append([InlineKeyboardButton("0️⃣ 🔙 رجوع", callback_data='main')]) # زر الرجوع الدائم
        await query.edit_message_text(f"{title}:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data == 'main':
        await show_main_menu(update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, show_main_menu))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    print("🚀 التصور النهائي شغال يا محمود!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
