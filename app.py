import os
import requests
import yt_dlp
import logging
from flask import Flask, request, make_response

# הגדרת לוגים
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# מפתח ה-AI שלך
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyDKYdB11968jqroePgfJe0IuDF2PntIyDQ')

def get_yt_link(query):
    """חיפוש מהיר ביוטיוב בשיטה הכי קלה לשרת"""
    # הגדרות אופטימליות למהירות
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'default_search': 'ytsearch1',
        'noplaylist': True,
        'nocheckcertificate': True,
        'extract_flat': True,
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # מחפש רק תוצאה אחת
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)['entries'][0]
            return info['url'], info.get('title', query)
        except Exception as e:
            logger.error(f"YouTube Error: {e}")
            return None, None

@app.route('/voice', methods=['POST', 'GET'])
def voice_logic():
    # קבלת הקלט מהטלפון
    val = request.values.get('val', '')
    logger.info(f"Received speech from phone: {val}")

    # אם המשתמש עדיין לא אמר כלום (או שהזיהוי התחיל)
    if not val or val == 'UNKNOWN' or val == '':
        # פקודה לימות המשיח: השמע טקסט וחכה לזיהוי דיבור (st)
        res_text = "read=t-נא לומר את שם השיר המבוקש=val,no,1,1,7,st"
    else:
        # המשתמש אמר משהו - נחפש ביוטיוב
        # הוספנו הודעת "מחפש" כדי שהמשתמש לא יחשוב שהשיחה נותקה
        audio_url, song_title = get_yt_link(val)
        
        if audio_url:
            # פקודה לניגון השיר
            # id_v_m=t-הודעה.playfile=לינק_ישיר
            res_text = f"id_v_m=t-מנגן כעת את {song_title}.playfile={audio_url}"
        else:
            res_text = "id_v_m=t-מצטער לא מצאתי את השיר המבוקש"

    # החזרת התשובה בפורמט טקסט נקי
    response = make_response(res_text)
    response.headers["Content-Type"] = "text/plain; charset=utf-8"
    return response

@app.route('/')
def home():
    return "Server is LIVE and Listening"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
