import os
import requests
import yt_dlp
import logging
from flask import Flask, request, make_response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# מפתח ה-AI שלך
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyDKYdB11968jqroePgfJe0IuDF2PntIyDQ')

def get_yt_link_fast(query):
    """חיפוש ביוטיוב - שיטה מהירה במיוחד ללא בדיקת תקינות מלאה כדי לחסוך זמן"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'default_search': 'ytsearch1',
        'noplaylist': True,
        'nocheckcertificate': True,
        'extract_flat': 'in_playlist',
        'skip_download': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)['entries'][0]
            return info['url'], info.get('title', query)
        except:
            return None, None

@app.route('/voice', methods=['POST', 'GET'])
def voice_logic():
    # קבלת הקלט מהטלפון
    val = request.values.get('val', '')
    logger.info(f"YEMOT_INPUT: {val}")

    # שלב 1: אם לא התקבל טקסט או שהזיהוי נכשל
    if not val or val == 'UNKNOWN' or val == '':
        # פקודה לימות המשיח: זיהוי דיבור חופשי (m)
        res_text = "read=t-נא לומר בבירור את שם השיר המבוקש=val,no,1,1,10,m"
    
    # שלב 2: אם התקבל טקסט - חיפוש וניגון מיידי
    else:
        logger.info(f"SEARCHING_FOR: {val}")
        audio_url, song_title = get_yt_link_fast(val)
        
        if audio_url:
            # התיקון: פקודת ניגון ישירה ונקייה
            res_text = f"id_v_m=t-מנגן את {song_title}.playfile={audio_url}"
        else:
            res_text = "id_v_m=t-לא הצלחתי למצוא את השיר ביוטיוב"

    # החזרת תשובה בפורמט טקסט פשוט
    response = make_response(res_text)
    response.headers["Content-Type"] = "text/plain; charset=utf-8"
    return response

@app.route('/')
def home():
    return "ONLINE"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
