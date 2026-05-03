from groq import Groq
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = '8569606909:AAEdLS1E5aruUZW60EPDThrWyGIsCUQlBNs'
GROQ_KEY = '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'
client = Groq(api_key=GROQ_KEY)

async def handle_message(update, context):
    user_text = update.message.text
    try:
        response = client.chat.completions.create(model='llama-3.3-70b-versatile',messages=[{'role':'system','content':'انت سكرتير محمود الشخصي ذكي وفرفوش وبترد بلهجة مصرية عامية شيك'},{'role':'user','content':user_text}])
        await update.message.reply_text(response.choices[0].message.content)
    except Exception as e:
        print(f'خطأ: {e}')
        await update.message.reply_text('حصل دروب!')

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print('البوت شغال!')
    app.run_polling()

if __name__ == '__main__':
    main()
