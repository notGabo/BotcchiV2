from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping
from typing import Any

import yt_dlp

from botcchi.config import Settings
from botcchi.models import Requester, Track
from botcchi.services.errors import MediaExtractionError

logger = logging.getLogger(__name__)


class _QuietLogger:
    def debug(self, message: str) -> None:
        logger.debug("yt-dlp: %s", message)

    def warning(self, message: str) -> None:
        logger.warning("yt-dlp: %s", message)

    def error(self, message: str) -> None:
        logger.error("yt-dlp: %s", message)


def _cookies_from_browser(value: str) -> tuple[str, str | None, str | None, str | None]:
    parts: list[str | None] = [part.strip() or None for part in value.split(":", 3)]
    parts.extend([None] * (4 - len(parts)))
    browser = parts[0]
    if browser is None:
        raise ValueError("COOKIES_BROWSER no puede estar vacio.")
    return browser, parts[1], parts[2], parts[3]


class YouTubeService:
    def __init__(self, settings: Settings) -> None:
        self._common_options: dict[str, Any] = {
            "format": "bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            "default_search": "ytsearch",
            "source_address": "0.0.0.0",
            "logger": _QuietLogger(),
        }
        if settings.cookies_file:
            self._common_options["cookiefile"] = str(settings.cookies_file)
        elif settings.cookies_browser:
            self._common_options["cookiesfrombrowser"] = _cookies_from_browser(
                settings.cookies_browser
            )

    async def resolve_track(self, query: str, requester: Requester) -> Track:
        try:
            info = await asyncio.to_thread(self._extract_track, query)
        except yt_dlp.utils.DownloadError as exc:
            raise MediaExtractionError(
                "No pude encontrar o procesar esa cancion en YouTube."
            ) from exc
        return self._to_track(info, requester)

    async def resolve_playlist(
        self, url: str, requester: Requester, *, limit: int = 100
    ) -> list[Track]:
        try:
            entries = await asyncio.to_thread(self._extract_playlist, url)
        except yt_dlp.utils.DownloadError as exc:
            raise MediaExtractionError(
                "No pude encontrar o procesar esa playlist de YouTube."
            ) from exc

        tracks = [
            self._to_track(entry, requester)
            for entry in entries[:limit]
            if entry and entry.get("id")
        ]
        if not tracks:
            raise MediaExtractionError("La playlist no contiene canciones disponibles.")
        return tracks

    async def stream_url(self, track: Track) -> str:
        try:
            info = await asyncio.to_thread(self._extract_track, track.playback_query)
        except yt_dlp.utils.DownloadError as exc:
            raise MediaExtractionError(
                f"No pude preparar '{track.display_title}' para reproducirla."
            ) from exc

        stream_url = info.get("url")
        if not stream_url:
            raise MediaExtractionError(
                f"YouTube no entrego audio para '{track.display_title}'."
            )
        return str(stream_url)

    def _extract_track(self, query: str) -> Mapping[str, Any]:
        target = query if self._looks_like_url(query) else f"ytsearch1:{query}"
        options = {**self._common_options, "noplaylist": True}
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(target, download=False)
        if info is None:
            raise yt_dlp.utils.DownloadError("No results")
        entries = info.get("entries") if isinstance(info, Mapping) else None
        if entries is not None:
            first = next((entry for entry in entries if entry), None)
            if first is None:
                raise yt_dlp.utils.DownloadError("No results")
            return first
        return info

    def _extract_playlist(self, url: str) -> list[Mapping[str, Any]]:
        options = {
            **self._common_options,
            "extract_flat": "in_playlist",
            "skip_download": True,
            "ignoreerrors": True,
            "noplaylist": False,
        }
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
        if not isinstance(info, Mapping) or not info.get("entries"):
            raise yt_dlp.utils.DownloadError("Not a playlist")
        return [entry for entry in info["entries"] if entry]

    @staticmethod
    def _looks_like_url(value: str) -> bool:
        return value.startswith(("http://", "https://"))

    @staticmethod
    def _to_track(info: Mapping[str, Any], requester: Requester) -> Track:
        video_id = str(info.get("id") or "")
        webpage_url = str(
            info.get("webpage_url")
            or info.get("original_url")
            or (f"https://www.youtube.com/watch?v={video_id}" if video_id else "")
        )
        duration = info.get("duration")
        return Track(
            title=str(info.get("title") or "Titulo desconocido"),
            webpage_url=webpage_url,
            playback_query=webpage_url,
            requester=requester,
            duration=int(duration) if duration is not None else None,
            uploader=str(
                info.get("uploader")
                or info.get("channel")
                or info.get("playlist_uploader")
                or "Desconocido"
            ),
            thumbnail=str(info.get("thumbnail")) if info.get("thumbnail") else None,
            source="youtube",
        )
