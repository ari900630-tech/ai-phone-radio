import os
import threading
import asyncio
import requests
import logging
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import yt_dlp
from twilio.twiml.voice_response import VoiceResponse

# הגדרת לוגים - כדי שנראה ב-Railway מה קורה
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# שליפת מפתחות
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '8655667831:AAEVUMmUocURtWKYj8Y9qrM1FpgErlRzz3w')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

# מצב המערכת
radio_state = {"url": None, "title": "לא נבחר שיר"}

def ai_identify_song(text):
    if not GEMINI_API_KEY: return text
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={GEMINI_API_KEY}"
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": f"Identify song: {text}. Return ONLY 'Artist - Name'"}]}]}, timeout=10).json()
        return res['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return text

def get_audio_url(query):
    ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'default_search': 'ytsearch', 'nocheckcertificate': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)['entries'][0]
            return info['url'], info.get('title', query)
        except Exception as e:
            logger.error(f"YouTube Error: {e}")
            return None, None

# --- בוט טלגרם ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    logger.info(f"Received message: {user_text}")
    m = await update.message.reply_text(f"🤖 ה-AI מנתח: {user_text}...")
    
    refined = ai_identify_song(user_text)
    url, title = get_audio_url(refined)
    
    if url:
        radio_state.update({"url": url, "title": title})
        await m.edit_text(f"✅ השיר מוכן!\n🎵 *{title}*\n\nחייג כעת ל-077-5558794.")
    else:
        await m.edit_text("❌ לא מצאתי את השיר. נסה שוב.")

def run_bot():
    logger.info("Starting Telegram Bot...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Bot Crash: {e}")

# --- שרת WEB ---
@app.route('/voice', methods=['POST'])
def voice():
    resp = VoiceResponse()
    if radio_state["url"]:
        resp.say(f"מנגן כעת את {radio_state['title']}.", language='he-IL')
        resp.play(radio_state["url"])
    else:
        resp.say("שלום. לא בחרת שיר בטלגרם. אנא שלח שיר ונסה שוב.", language='he-IL')
    return str(resp)

@app.route('/')
def health():
    return "Server is LIVE"

if __name__ == "__main__":
    # הפעלת הבוט בנפרד
    threading.Thread(target=run_bot, daemon=True).start()
    # הרצת השרת
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting Flask on port {port}")
    app.run(host='0.0.0.0', port=port)