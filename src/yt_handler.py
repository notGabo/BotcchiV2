import yt_dlp
import asyncio
import os
from os import getenv
from dotenv import load_dotenv
load_dotenv()

COOKIES_FILE = getenv("COOKIES_FILE")
COOKIE_BROWSER = getenv("COOKIE_BROWSER")

# Verificar si el archivo de cookies existe
if COOKIES_FILE and os.path.isfile(COOKIES_FILE):
    print(f"Usando archivo de cookies: {COOKIES_FILE}")
else:
    print(f"Advertencia: El archivo de cookies no existe o no está especificado: {COOKIES_FILE}")

async def buscador_ytdlp_async(query,ydl_opts):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: _extract(query,ydl_opts))

def _extract(query, ydl_opts):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            return info
        except yt_dlp.utils.DownloadError as e:
            print(f"Error al extraer información: {e}")
            return None

def ytdlp_opts(playlist: bool | None):
    opts = {
        "format": "bestaudio/best",
        "noplaylist": playlist,
        "youtube_include_dash_manifest": False,
        "youtubeinclude_hls_manifest": False,
    }

    if COOKIES_FILE and os.path.isfile(COOKIES_FILE):
        opts["cookiefile"] = COOKIES_FILE
        opts["cookiesfrombrowser"] = COOKIE_BROWSER

    return opts