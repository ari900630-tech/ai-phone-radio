import os
import requests
import yt_dlp
import logging
import random
from flask import Flask, request, make_response
from firebase_admin import credentials, firestore, initialize_app, _apps

# הגדרת לוגים
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- אתחול Firebase Firestore ---
try:
    # הגדרות סביבה מ-Railway (Firestore Config)
    if not _apps:
        initialize_app()
    db = firestore.client()
    app_id = os.environ.get('APP_ID', 'radio-ai-yemot')
    logger.info("Firestore connected successfully")
except Exception as e:
    logger.error(f"Firestore error: {e}")
    db = None

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyDKYdB11968jqroePgfJe0IuDF2PntIyDQ')

def get_ai_recommendation(likes_list):
    """שימוש בבינה מלאכותית להמלצה על שיר לפי היסטוריית הלייקים"""
    if not likes_list:
        # רשימת ברירת מחדל אם אין עדיין לייקים
        return random.choice(["עומר אדם", "חנן בן ארי", "ישי ריבו", "עדן חסון", "נועה קירל"])
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={GEMINI_API_KEY}"
    
    # הפרומפט ל-AI: תנתח מה המשתמש אוהב ותציע משהו דומה
    likes_str = ", ".join(likes_list[-10:]) # לוקח את 10 הלייקים האחרונים
    prompt = f"The user likes these artists/songs: {likes_str}. Recommend ONE similar popular artist or song name. Return ONLY the name in Hebrew."
    
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=4).json()
        recommendation = res['candidates'][0]['content']['parts'][0]['text'].strip()
        return recommendation
    except:
        return random.choice(likes_list)

def get_yt_audio(query):
    """מציאת קישור להשמעה מיוטיוב"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'default_search': 'ytsearch3',
        'noplaylist': True,
        'nocheckcertificate': True,
        'extract_flat': True,
        'skip_download': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch3:{query}", download=False)
            entry = random.choice(info['entries'])
            return entry['url'], entry.get('title', query)
        except:
            return None, None

@app.route('/voice', methods=['POST', 'GET'])
def voice():
    # נתונים מימות המשיח
    digits = request.values.get('Digits', '')
    phone = request.values.get('ApiPhone', 'unknown_user')
    current_song = request.values.get('current_song', '') # שם האמן/שיר שמתנגן כרגע
    
    # 1. שליפת נתוני המשתמש מהענן
    user_likes = []
    if db:
        user_ref = db.collection('artifacts').document(app_id).collection('users').document(phone).collection('data').document('profile')
        doc = user_ref.get()
        if doc.exists:
            user_likes = doc.to_dict().get('likes', [])

    # --- מקש 2: לייק (שמירה לענן) ---
    if digits == '2' and current_song:
        if current_song not in user_likes:
            user_likes.append(current_song)
            if db:
                user_ref.set({'likes': user_likes}, merge=True)
        return make_response("id_v_m=t-השיר נוסף למועדפים שלך. המערכת לומדת את הטעם שלך. 1 לשיר הבא.")

    # --- מקש 1 או כניסה: המלצת AI וניגון ---
    # ה-AI מחליט מה לנגן לפי הלייקים ששמורים בענן
    recommended_artist = get_ai_recommendation(user_likes)
    audio_url, title = get_yt_audio(recommended_artist)

    if audio_url:
        # אנחנו שולחים את שם האמן כפרמטר 'current_song' כדי שנוכל לעשות לו לייק בלחיצה הבאה
        response_text = f"id_v_m=t-לפי הטעם שלך, בחרתי להשמיע את {recommended_artist}. 1 להחלפה. 2 ללייק..playfile={audio_url}&current_song={recommended_artist}"
    else:
        response_text = "id_v_m=t-מצטער, הייתה שגיאה בחיבור. הקש 1 לניסיון חוזר."

    res = make_response(response_text)
    res.headers["Content-Type"] = "text/plain; charset=utf-8"
    return res

@app.route('/')
def home():
    return "Music AI Cloud Server is running"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
