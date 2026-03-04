import os
import requests
import yt_dlp
import logging
import random
from flask import Flask, request, make_response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

ARTISTS = ["חנן בן ארי", "עומר אדם", "עדן חסון", "ישי ריבו", "אושר כהן", "פאר טסי"]

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
            info = ydl.extract_info(f"ytsearch1:{query} שירים", download=False)['entries'][0]
            return info['url'], info.get('title', query)
        except:
            return None, None

@app.route('/voice', methods=['POST', 'GET'])
def voice():
    digits = request.values.get('Digits', '')
    logger.info(f"Digits: {digits}")

    artist = random.choice(ARTISTS)
    link, title = get_yt_link(artist)

    if link:
        response_text = f"id_v_m=t-מנגן את {artist}. 1 להחלפה. 2 ללייק..playfile={link}"
    else:
        response_text = "go_to_folder=/1"

    response = make_response(response_text)
    response.headers["Content-Type"] = "text/plain; charset=utf-8"
    return response

@app.route('/')
def home():
    return "Server Active"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
