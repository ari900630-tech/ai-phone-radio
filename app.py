import os
import requests
import yt_dlp
import logging
from flask import Flask, request, make_response

# הגדרת לוגים - כדי לראות מה קורה בזמן אמת ב-Railway
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# מפתח ה-AI שלך
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyDKYdB11968jqroePgfJe0IuDF2PntIyDQ')

def get_fast_song_info(text):
    """שימוש ב-AI להבנה מהירה של שם השיר"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={GEMINI_API_KEY}"
    try:
        # זמן המתנה קצר מאוד ל-AI
        res = requests.post(url, json={"contents": [{"parts": [{"text": f"Song: {text}. Return ONLY 'Artist - Name'"}]}]}, timeout=2).json()
        return res['candidates'][0]['content']['parts'][0]['text'].strip()
    except:
        return text

def get_youtube_stream(query):
    """חיפוש ביוטיוב בשיטה המהירה ביותר (Flat Extract)"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'default_search': 'ytsearch1',
        'noplaylist': True,
        'nocheckcertificate': True,
        'extract_flat': True,
        'skip_download': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)['entries'][0]
            # מחזיר את הלינק הישיר שיוטיוב נותן
            return info['url'], info.get('title', query)
        except Exception as e:
            logger.error(f"YT Error: {e}")
            return None, None

@app.route('/voice', methods=['POST', 'GET'])
def voice_logic():
    # קבלת הפרמטר val מימות המשיח
    val = request.values.get('val', '')
    logger.info(f"Yemot Input: {val}")

    # שלב 1: בקשת קלט מהמשתמש
    if not val or val == 'UNKNOWN' or val == '':
        response_text = "read=t-נא לומר את שם השיר המבוקש=val,no,1,1,7,st"
    
    # שלב 2: עיבוד השיר וניגון
    else:
        logger.info(f"Processing request for: {val}")
        # ה-AI מוודא מה השם הנכון
        refined_name = get_fast_song_info(val)
        # מוצאים לינק ביוטיוב
        audio_url, song_title = get_youtube_stream(refined_name)
        
        if audio_url:
            # פקודה לימות המשיח: השמעה וניגון
            response_text = f"id_v_m=t-מנגן כעת את {song_title}.playfile={audio_url}"
        else:
            response_text = "id_v_m=t-מצטער, לא מצאתי את השיר ביוטיוב"

    # החזרת התשובה בפורמט טקסט נקי בלבד
    res = make_response(response_text)
    res.headers["Content-Type"] = "text/plain; charset=utf-8"
    return res

@app.route('/')
def health():
    return "Server is LIVE"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
