import os
from dotenv import load_dotenv

load_dotenv()


def _parse_int_list(env_var_name):
    return [
        int(value.strip())
        for value in os.getenv(env_var_name, "").split(",")
        if value.strip()
    ]

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BOT_PREFIX = os.getenv("BOT_PREFIX", "--")
APP_ID = os.getenv("APP_ID", "")
PUBLIC_KEY = os.getenv("PUBLIC_KEY", "")
BOT_URL_INVITACION = os.getenv("BOT_URL_INVITACION", "")

BOT_SERVIDORES_PERMITIDOS = _parse_int_list("BOT_SERVIDORES_PERMITIDOS")
BOT_SERVIDORES_MANTENER_CONECTADO = _parse_int_list("BOT_SERVIDORES_MANTENER_CONECTADO")

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
COOKIES_BROWSER = os.getenv("COOKIES_BROWSER", "")
COOKIES_FILE = os.getenv("COOKIES_FILE", "")
