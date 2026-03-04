import os
import requests
import yt_dlp
import logging
import time
from flask import Flask, request, make_response

# הגדרת לוגים - כדי שתוכל לראות ב-Railway מה קורה
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# מפתח ה-AI שלך
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyDKYdB11968jqroePgfJe0IuDF2PntIyDQ')

def get_song_refined(text):
    """שימוש ב-AI להבנה מהירה של שם השיר"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={GEMINI_API_KEY}"
    try:
        # הגבלת זמן תגובה ל-AI ל-2 שניות
        res = requests.post(url, json={"contents": [{"parts": [{"text": f"Identify song: {text}. Return ONLY 'Artist - Name' in Hebrew"}]}]}, timeout=2).json()
        return res['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return text

def get_youtube_url(query):
    """חיפוש מהיר ביוטיוב ללא הורדה"""
    # הגדרות חיפוש מהירות במיוחד
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'default_search': 'ytsearch1',
        'noplaylist': True,
        'nocheckcertificate': True,
        'extract_flat': 'in_playlist', # מהירות גבוהה יותר
        'skip_download': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)['entries'][0]
            # שליפת לינק ישיר להשמעה (מניעת הפניה)
            return info['url'], info.get('title', query)
        except Exception as e:
            logger.error(f"YouTube Error: {e}")
            return None, None

@app.route('/voice', methods=['POST', 'GET'])
def voice_logic():
    # קבלת הפרמטר מימות המשיח
    val = request.values.get('val', '')
    logger.info(f"Received call data: val={val}")

    # אם המשתמש לא אמר כלום או שהזיהוי התחיל מחדש
    if not val or val == 'UNKNOWN' or val == '':
        # פקודה לימות המשיח: בקש מהמשתמש להגיד שם שיר וחכה לדיבור (st)
        res_text = "read=t-נא לומר את שם השיר המבוקש=val,no,1,1,7,st"
    else:
        # שלב העיבוד - הוספנו מדידת זמן כדי לוודא שלא עוברים את ה-7 שניות של ימות המשיח
        start_time = time.time()
        
        # 1. עיבוד עם AI
        refined_query = get_song_refined(val)
        logger.info(f"AI suggested: {refined_query}")
        
        # 2. חיפוש ביוטיוב
        audio_url, audio_title = get_youtube_url(refined_query)
        
        end_time = time.time()
        logger.info(f"Processing took {end_time - start_time:.2f} seconds")

        if audio_url:
            # פקודה לימות המשיח: השמע טקסט ונגן את הלינק הישיר
            # id_v_m=t-טקסט.playfile=לינק
            res_text = f"id_v_m=t-מנגן כעת את {audio_title}.playfile={audio_url}"
        else:
            res_text = "id_v_m=t-מצטער לא מצאתי את השיר ביוטיוב"

    # החזרת התשובה בפורמט טקסט נקי
    response = make_response(res_text)
    response.headers["Content-Type"] = "text/plain; charset=utf-8"
    return response

@app.route('/')
def health():
    return "AI Radio is LIVE"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
