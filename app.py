import os
import requests
import yt_dlp
import logging
from flask import Flask, request, make_response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyDKYdB11968jqroePgfJe0IuDF2PntIyDQ')

def get_ai_refined(text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={GEMINI_API_KEY}"
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": f"Identify song: {text}. Return ONLY 'Artist - Name' in Hebrew"}]}]}, timeout=3).json()
        return res['candidates'][0]['content']['parts'][0]['text'].strip()
    except:
        return text

def get_yt_link(query):
    opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'default_search': 'ytsearch1',
        'noplaylist': True,
        'nocheckcertificate': True,
        'extract_flat': True
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)['entries'][0]
            # התיקון: מוודא שמחזירים לינק ישיר ומהיר
            return info['url'], info.get('title', query)
        except:
            return None, None

@app.route('/voice', methods=['POST', 'GET'])
def voice_logic():
    val = request.values.get('val', '')
    logger.info(f"Call input: {val}")

    if not val or val == 'UNKNOWN' or val == '':
        # שלב א: בקשת קלט
        res_text = "read=t-נא לומר את שם השיר המבוקש=val,no,1,1,7,st"
    else:
        # שלב ב: חיפוש וניגון
        refined = get_ai_refined(val)
        link, title = get_yt_link(refined)
        
        if link:
            # התיקון: מבנה פקודה תקני לימות המשיח
            res_text = f"id_v_m=t-מנגן כעת את {title}.playfile={link}"
        else:
            res_text = "id_v_m=t-מצטער לא מצאתי את השיר"

    response = make_response(res_text)
    response.headers["Content-Type"] = "text/plain; charset=utf-8"
    return response

@app.route('/')
def health():
    return "Server is LIVE"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
