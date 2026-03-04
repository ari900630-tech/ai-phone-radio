import os
import threading
import asyncio
import requests
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import yt_dlp

# הגדרת לוגים - כדי שנוכל לראות ב-Railway אם יש בעיות
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# שליפת מפתחות מהגדרות המערכת
# הטוקן של טלגרם שכבר נתת לי קודם
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '8655667831:AAEVUMmUocURtWKYj8Y9qrM1FpgErlRzz3w')
# המפתח של גוגל ששלחת עכשיו
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyDKYdB11968jqroePgfJe0IuDF2PntIyDQ')

# משתנה לשמירת השיר שנבחר בטלגרם
radio_state = {"url": None, "title": "לא נבחר שיר"}

def ai_process_song(text):
    """שימוש בבינה מלאכותית להבנת שם השיר"""
    if not GEMINI_API_KEY:
        logger.warning("Missing Gemini API Key!")
        return text
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={GEMINI_API_KEY}"
    prompt = f"Identify the song: '{text}'. Return ONLY 'Artist - Song Name' in Hebrew or English."
    
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=10).json()
        ai_suggestion = res['candidates'][0]['content']['parts'][0]['text'].strip()
        logger.info(f"AI interpreted: {ai_suggestion}")
        return ai_suggestion
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return text

def get_audio_from_youtube(query):
    """חיפוש ביוטיוב ושליפת לינק להזרמה"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'default_search': 'ytsearch1',
        'nocheckcertificate': True,
        'noplaylist': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)['entries'][0]
            return info['url'], info.get('title', query)
        except Exception as e:
            logger.error(f"YouTube Error: {e}")
            return None, None

# --- בוט טלגרם ---
async def handle_telegram_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    logger.info(f"Telegram user requested: {user_text}")
    
    status_msg = await update.message.reply_text(f"🤖 ה-AI מנתח את הבקשה: {user_text}...")
    
    refined = ai_process_song(user_text)
    url, title = get_audio_from_youtube(refined)
    
    if url:
        radio_state.update({"url": url, "title": title})
        await status_msg.edit_text(f"✅ השיר מוכן!\n🎵 *{title}*\n\nחייג כעת ל-074-7954941 והקש 1.")
    else:
        await status_msg.edit_text("❌ לא מצאתי את השיר. נסה שוב.")

def start_telegram_bot():
    """הפעלת הבוט ב-Thread נפרד"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        bot = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_telegram_message))
        bot.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Bot Crash: {e}")

# --- ממשק ימות המשיח ---
@app.route('/voice', methods=['POST', 'GET'])
def voice_api():
    """הנתיב שאליו ימות המשיח פונים"""
    if radio_state["url"]:
        # פקודה לימות המשיח להשמיע את השם ולנגן את הקובץ
        return f"id_v_m=t-מנגן כעת את {radio_state['title']}.playfile={radio_state['url']}"
    else:
        return "id_v_m=t-שלום. עדיין לא בחרת שיר בטלגרם. אנא שלח שם שיר לבוט ונסה שוב."

@app.route('/')
def health():
    return f"AI Radio is LIVE. Current Song: {radio_state['title']}"

if __name__ == "__main__":
    # הפעלת הבוט
    threading.Thread(target=start_telegram_bot, daemon=True).start()
    # הפעלת שרת ה-Web
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)