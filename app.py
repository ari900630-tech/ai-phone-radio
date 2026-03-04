import os
import requests
import yt_dlp
import logging
from flask import Flask, request, make_response

# הגדרת לוגים - כדי שתוכל לראות ב-Railway מה קורה בזמן אמת
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# שליפת מפתח ה-AI מהגדרות המערכת ב-Railway
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyDKYdB11968jqroePgfJe0IuDF2PntIyDQ')

def get_refined_song(user_speech):
    """משתמש ב-Gemini כדי להבין מה השיר המדויק מתוך הדיבור"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={GEMINI_API_KEY}"
    prompt = f"The user said: '{user_speech}'. Identify the song and artist. Return ONLY 'Artist - Song Name' in Hebrew."
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=5).json()
        return res['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return user_speech

def get_youtube_audio(query):
    """מוצא לינק ישיר להשמעת אודיו מיוטיוב"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'default_search': 'ytsearch1',
        'noplaylist': True,
        'nocheckcertificate': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)['entries'][0]
            return info['url'], info.get('title', query)
        except Exception as e:
            logger.error(f"YouTube Error: {e}")
            return None, None

@app.route('/voice', methods=['POST', 'GET'])
def voice_endpoint():
    """הנקודה שאליה מתחברת המערכת של ימות המשיח"""
    val = request.values.get('val', '')
    
    # שלב 1: אם המשתמש עוד לא אמר כלום, נבקש ממנו לדבר
    if not val or val == 'UNKNOWN':
        # הפקודה read אומרת לימות המשיח להשמיע טקסט ולחכות לזיהוי דיבור (st)
        response_text = "read=t-נא לומר את שם השיר המבוקש=val,no,1,1,7,st"
    else:
        # שלב 2: עיבוד הדיבור עם AI וחיפוש ביוטיוב
        song_query = get_refined_song(val)
        audio_url, audio_title = get_youtube_audio(song_query)
        
        if audio_url:
            # שלב 3: שליחת פקודת ניגון ישירה לטלפון
            response_text = f"id_v_m=t-מנגן כעת את {audio_title}.playfile={audio_url}"
        else:
            response_text = "id_v_m=t-מצטער לא מצאתי את השיר המבוקש"

    # החזרת התשובה בפורמט טקסט נקי שימות המשיח מבינים
    res = make_response(response_text)
    res.headers["Content-Type"] = "text/plain; charset=utf-8"
    return res

@app.route('/')
def health_check():
    return "Server is LIVE - Ready for Yemot HaMashiach"

if __name__ == "__main__":
    # הפעלה על הפורט ש-Railway נותן לנו
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
