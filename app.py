import os
import requests
import yt_dlp
import logging
from flask import Flask, request, make_response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyDKYdB11968jqroePgfJe0IuDF2PntIyDQ')

def get_yt_link(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'default_search': 'ytsearch1',
        'noplaylist': True,
        'nocheckcertificate': True,
        'extract_flat': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)['entries'][0]
            return info['url'], info.get('title', query)
        except: return None, None

@app.route('/voice', methods=['POST', 'GET'])
def voice_logic():
    # קבלת הערך - ניקוי רשימות אם נשלחו כמה ערכים
    vals = request.values.getlist('val')
    val = vals[0] if vals else ''
    
    logger.info(f"RECEIVED_VAL: {val}")

    # אם המשתמש לא אמר כלום או שהזיהוי נכשל
    if not val or val.upper() == 'UNKNOWN' or val == '1':
        # ננסה שיטת זיהוי אחרת (כאן השינוי - m במקום st)
        res_text = "read=t-נא לומר שוב את שם השיר המבוקש=val,no,1,1,10,m"
    else:
        logger.info(f"FINDING_SONG: {val}")
        link, title = get_yt_link(val)
        if link:
            res_text = f"id_v_m=t-מנגן את {title}.playfile={link}"
        else:
            res_text = "id_v_m=t-לא מצאתי את השיר"

    response = make_response(res_text)
    response.headers["Content-Type"] = "text/plain; charset=utf-8"
    return response

@app.route('/')
def home(): return "OK"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
