import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BOT_PREFIX = os.getenv("BOT_PREFIX", "--")
APP_ID = os.getenv("APP_ID", "")
PUBLIC_KEY = os.getenv("PUBLIC_KEY", "")
BOT_URL_INVITACION = os.getenv("BOT_URL_INVITACION", "")

BOT_SERVIDORES_PERMITIDOS = [
    int(sid.strip())
    for sid in os.getenv("BOT_SERVIDORES_PERMITIDOS", "").split(",")
    if sid.strip()
]

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
COOKIES_BROWSER = os.getenv("COOKIES_BROWSER", "")
COOKIES_FILE = os.getenv("COOKIES_FILE", "")
