import os
import requests
import yt_dlp
import logging
from flask import Flask, request, make_response

# לוגים - לבדיקה ב-Railway
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# מפתח ה-AI שלך
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyDKYdB11968jqroePgfJe0IuDF2PntIyDQ')

def get_song(text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={GEMINI_API_KEY}"
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": f"Identify song: {text}. Return ONLY 'Artist - Name'"}]}]}, timeout=3).json()
        return res['candidates'][0]['content']['parts'][0]['text'].strip()
    except:
        return text

def get_url(q):
    opts = {'format': 'bestaudio/best', 'quiet': True, 'default_search': 'ytsearch1', 'noplaylist': True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch1:{q}", download=False)['entries'][0]
            return info['url'], info.get('title', q)
        except:
            return None, None

@app.route('/voice', methods=['POST', 'GET'])
def voice():
    # שליפת הפרמטר שימות המשיח שולחים
    val = request.values.get('val', '')
    logger.info(f"Yemot Request: val={val}")

    if not val or val == 'UNKNOWN' or val == '':
        # פקודה ראשונה: לבקש מהמשתמש להגיד שם שיר
        res_text = "read=t-נא לומר שם שיר=val,no,1,1,7,st"
    else:
        # פקודה שנייה: עיבוד וניגון
        song = get_song(val)
        link, title = get_url(song)
        if link:
            res_text = f"id_v_m=t-מנגן את {title}.playfile={link}"
        else:
            res_text = "id_v_m=t-לא מצאתי שיר"

    # התיקון הקריטי: החזרת טקסט נקי בלבד
    response = make_response(res_text)
    response.headers["Content-Type"] = "text/plain; charset=utf-8"
    return response

@app.route('/')
def health():
    return "OK"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
