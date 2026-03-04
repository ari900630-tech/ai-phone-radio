import os
import requests
import yt_dlp
import logging
import random
from flask import Flask, request, make_response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# רשימת זמרים להתחלה מהירה
INITIAL_ARTISTS = ["חנן בן ארי", "עומר אדם", "עדן חסון", "ישי ריבו", "אושר כהן"]

def get_yt_link(query):
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
            return info['url'], info.get('title', query)
        except:
            return None, None

@app.route('/voice', methods=['POST', 'GET'])
def voice():
    digits = request.values.get('Digits', '')
    phone = request.values.get('ApiPhone', 'unknown')
    current_song = request.values.get('current_song', '')

    logger.info(f"Phone: {phone}, Digits: {digits}, Current: {current_song}")

    # מקש 2 - לייק
    if digits == '2' and current_song:
        # כאן אפשר להוסיף שמירה ל-DB. בינתיים נחזיר אישור
        res_text = f"id_v_m=t-סימנתי שאהבת את {current_song}. נמשיך במוזיקה.go_to_folder=/1"
        return make_response(res_text)

    # ברירת מחדל: בחר זמר אקראי (או המלצה בעתיד)
    artist = random.choice(INITIAL_ARTISTS)
    link, title = get_yt_link(artist)

    if link:
        # פקודת ההשמעה הישירה
        res_text = f"id_v_m=t-מנגן את {artist}. 1 להחלפה, 2 ללייק..playfile={link}&current_song={artist}"
    else:
        res_text = "id_v_m=t-תקלה זמנית בחיבור, נסה שוב.go_to_folder=/1"

    response = make_response(res_text)
    response.headers["Content-Type"] = "text/plain; charset=utf-8"
    return response

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
