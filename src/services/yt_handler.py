import asyncio
import yt_dlp
from src.config import COOKIES_FILE, COOKIES_BROWSER


class YTDLSource:
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch',
        'source_address': '0.0.0.0',
    }

    AGE_RESTRICTED_PATTERNS = (
        'sign in to confirm your age',
        'confirm your age',
        'this video may be inappropriate for some users',
    )

    if COOKIES_FILE:
        YTDL_OPTIONS['cookiefile'] = COOKIES_FILE
    elif COOKIES_BROWSER:
        YTDL_OPTIONS['cookiesfrombrowser'] = (COOKIES_BROWSER,)

    ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

    @staticmethod
    def _build_search_query(query: str, add_topic: bool = False) -> str:
        prepared = query.strip()
        if not prepared:
            return prepared
        lowered = prepared.lower()
        if add_topic and not lowered.endswith(' topic'):
            return f"{prepared} topic"
        return prepared

    @classmethod
    def _is_age_restricted_error(cls, error: Exception) -> bool:
        message = str(error).lower()
        return any(pattern in message for pattern in cls.AGE_RESTRICTED_PATTERNS)

    @classmethod
    async def extract_info(cls, query: str, download: bool = False, status_callback=None):
        attempts = [cls._build_search_query(query)]
        if not attempts[0].lower().endswith(' topic'):
            attempts.append(cls._build_search_query(query, add_topic=True))

        total_attempts = len(attempts)
        last_error = None

        for index, attempt in enumerate(attempts, start=1):
            try:
                # Si es un reintento (ej. restricción de edad en el 1er intento), notificar a Discord
                if status_callback and index > 1:
                    await status_callback(
                        f"⚠️ **Restricción de edad / error detectado.**\nReintentando ({index}/{total_attempts}) con búsqueda alternativa: `{attempt}`..."
                    )

                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(
                    None, lambda current_query=attempt: cls.ytdl.extract_info(current_query, download=download)
                )

                if not data:
                    raise yt_dlp.utils.DownloadError("La búsqueda de YouTube no devolvió resultados.")

                if 'entries' in data:
                    data = data['entries'][0]

                if data is None:
                    raise yt_dlp.utils.DownloadError("La búsqueda de YouTube devolvió una entrada vacía.")

                seconds = data.get('duration', 0) or 0
                mins, secs = divmod(seconds, 60)

                return {
                    'url': data.get('url', ''),
                    'webpage_url': data.get('webpage_url', ''),
                    'title': data.get('title', 'Desconocido'),
                    'thumbnail': data.get('thumbnail', ''),
                    'duration_str': f"{mins}:{secs:02d}",
                    'uploader': data.get('uploader', 'Canal Desconocido')
                }
            except Exception as exc:
                last_error = exc
                if cls._is_age_restricted_error(exc) and attempt == attempts[0]:
                    continue
                break

        if last_error is not None:
            raise RuntimeError(
                f"No se pudo obtener la canción tras ({total_attempts}/{total_attempts}) intentos.\n"
                f"**Detalle:** `{last_error}`"
            ) from last_error

        raise RuntimeError(f"No se pudo obtener la canción: {query}.")