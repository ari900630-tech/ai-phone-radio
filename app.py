import os
import requests
import yt_dlp
import logging
import random
from flask import Flask, request, make_response

# הגדרת לוגים
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# רשימות זמרים פופולריים
ARTISTS_HEBREW = {
    "1": "עומר אדם",
    "2": "אייל גולן",
    "3": "עדן חסון",
    "4": "חנן בן ארי",
    "5": "ישי ריבו",
    "6": "אושר כהן",
    "7": "נועה קירל",
    "8": "ששון איפרם שאולוב",
    "9": "בניה ברבי"
}

ARTISTS_ENGLISH = {
    "1": "Taylor Swift",
    "2": "The Weeknd",
    "3": "Drake",
    "4": "Ed Sheeran",
    "5": "Justin Bieber",
    "6": "Bruno Mars",
    "7": "Adele",
    "8": "Dua Lipa",
    "9": "Billie Eilish"
}

def get_yt_link(query):
    """חיפוש מהיר ביוטיוב עם גיוון תוצאות"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'default_search': 'ytsearch10', # מחפש 10 תוצאות כדי לבחור אחת אקראית
        'noplaylist': True,
        'nocheckcertificate': True,
        'extract_flat': True,
        'skip_download': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            search_query = f"{query} songs"
            info = ydl.extract_info(f"ytsearch10:{search_query}", download=False)
            # בחירת שיר אקראי מתוך ה-10 שנמצאו
            entry = random.choice(info['entries'])
            return entry['url'], entry.get('title', query)
        except Exception as e:
            logger.error(f"Error fetching YouTube link: {e}")
            return None, None

@app.route('/voice', methods=['POST', 'GET'])
def voice_logic():
    digits = request.values.get('Digits', '')
    step = request.values.get('step', 'play') # play, select_lang, select_artist
    lang = request.values.get('lang', 'he') # he, en
    
    logger.info(f"Digits: {digits}, Step: {step}, Lang: {lang}")

    # תפריט בחירת שפה (כפתור 3 מהתפריט הראשי)
    if digits == '3' or step == 'select_lang':
        res_text = "read=t-לבחירת זמרים בעברית הקש 1. לזמרים באנגלית הקש 2.=lang_choice,no,1,1,1,#"
        # מעבר לשלב הבא
        res_text = res_text.replace("lang_choice", "Digits")
        response = make_response(res_text + f"&step=select_artist")
        response.headers["Content-Type"] = "text/plain; charset=utf-8"
        return response

    # בחירת זמר ספציפי
    if step == 'select_artist':
        current_lang = "en" if digits == "2" else "he"
        artists_list = ARTISTS_ENGLISH if current_lang == "en" else ARTISTS_HEBREW
        
        prompt = "נא להקיש את מספר הזמר: "
        for k, v in artists_list.items():
            prompt += f"{k} ל{v}. "
        
        res_text = f"read=t-{prompt}=artist_choice,no,1,1,1,#"
        res_text = res_text.replace("artist_choice", "Digits")
        response = make_response(res_text + f"&step=play&lang={current_lang}")
        response.headers["Content-Type"] = "text/plain; charset=utf-8"
        return response

    # לייק (כפתור 2)
    if digits == '2':
        res_text = "id_v_m=t-השיר נוסף למועדפים. להמשך הקש 1."
        response = make_response(res_text)
        response.headers["Content-Type"] = "text/plain; charset=utf-8"
        return response

    # ניגון שיר (כפתור 1 או אחרי בחירת זמר)
    current_artists = ARTISTS_ENGLISH if lang == "en" else ARTISTS_HEBREW
    # אם המשתמש הקיש מספר זמר, נשתמש בו. אם לא, נבחר אקראי מהרשימה הנוכחית.
    artist_name = current_artists.get(digits, random.choice(list(current_artists.values())))
    
    audio_url, song_title = get_yt_link(artist_name)
    
    if audio_url:
        res_text = f"id_v_m=t-מנגן כעת שיר של {artist_name}. שיר: {song_title}. להעברה הקש 1. ללייק הקש 2. לבחירת זמר הקש 3..playfile={audio_url}"
    else:
        res_text = "id_v_m=t-לא הצלחתי למצוא שיר, מנסה שוב. הקש 1."

    response = make_response(res_text + f"&lang={lang}&step=play")
    response.headers["Content-Type"] = "text/plain; charset=utf-8"
    return response

@app.route('/')
def home():
    return "AI Music Station is Live"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
