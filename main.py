from groq import Groq
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import requests
from datetime import datetime
import pytz

TELEGRAM_TOKEN = "8569606909:AAEdLS1E5aruUZW60EPDThrWyGIsCUQlBNs"
GROQ_KEY = "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"
WEATHER_KEY = "b40b5f5b6b6b6b6b6b6b6b6b6b6b6b6b"

client = Groq(api_key=GROQ_KEY)
conversation_history = []

def get_datetime():
    egypt_tz = pytz.timezone('Africa/Cairo')
    now = datetime.now(egypt_tz)
    
    days_ar = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
    months_ar = ["يناير", "فبراير", "مارس", "إبريل", "مايو", "يونيو", 
                 "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
    
    day_name = days_ar[now.weekday()]
    date_str = f"{now.day} {months_ar[now.month-1]} {now.year}"
    time_str = now.strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م")
    
    return day_name, date_str, time_str

def get_weather():
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q=Cairo&appid={WEATHER_KEY}&units=metric&lang=ar"
        response = requests.get(url)
        data = response.json()
        temp = round(data['main']['temp'])
        desc = data['weather'][0]['description']
        return f"{temp}°C - {desc}"
    except:
        return "مش متاح دلوقتي"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    day_name, date_str, time_str = get_datetime()
    weather = get_weather()
    
    status_bar = f"📅 {day_name} {date_str} | 🕐 {time_str} | 🌡️ {weather}"
    
    conversation_history.append({"role": "user", "content": user_text})
    
    if len(conversation_history) > 20:
        conversation_history.pop(0)
    
    system_prompt = f"""أنت سكرتير محمود الشخصي، ذكي وفرفوش وبترد بلهجة مصرية عامية شيك.
ناديه دايماً بـ "محمود".
لو طلب ترجمة، ترجملهوله على طول.
المعلومات الحالية: {status_bar}"""
    
    messages = [{"role": "system", "content": system_prompt}] + conversation_history
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages
        )
        bot_response = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": bot_response})
        
        full_response = f"{status_bar}\n{'─'*30}\n{bot_response}"
        await update.message.reply_text(full_response)
        
    except Exception as e:
        print(f"خطأ: {e}")
        await update.message.reply_text("حصل دروب يا محمود، بعت تاني!")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("البوت شغال يا محمود!")
    app.run_polling()

if __name__ == "__main__":
    main()
