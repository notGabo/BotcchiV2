import yt_dlp
import asyncio
from os import getenv
from dotenv import load_dotenv
load_dotenv()

COOKIES_FILE = getenv("COOKIES_FILE")

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
    return {
        "format": "bestaudio/best",
        "noplaylist": playlist,
        "youtube_include_dash_manifest": False,
        "youtubeinclude_hls_manifest": False,
        "cookiefile": COOKIES_FILE,
    }