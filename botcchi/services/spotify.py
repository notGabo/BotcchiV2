from __future__ import annotations

import asyncio
import re
from collections.abc import Mapping
from typing import Any

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from botcchi.config import Settings
from botcchi.models import Requester, Track
from botcchi.services.errors import MediaExtractionError, SpotifyNotConfiguredError

SPOTIFY_URL = re.compile(
    r"https?://open\.spotify\.com/(?:intl-[a-z-]+/)?(?P<kind>track|playlist)/(?P<id>[A-Za-z0-9]+)"
)


class SpotifyService:
    def __init__(self, settings: Settings) -> None:
        self._client: spotipy.Spotify | None = None
        if settings.spotify_enabled:
            auth = SpotifyClientCredentials(
                client_id=settings.spotify_client_id,
                client_secret=settings.spotify_client_secret,
            )
            self._client = spotipy.Spotify(auth_manager=auth, requests_timeout=15)

    @staticmethod
    def parse_url(url: str) -> tuple[str, str] | None:
        match = SPOTIFY_URL.match(url.strip())
        if not match:
            return None
        return match.group("kind"), match.group("id")

    async def resolve_track(self, url: str, requester: Requester) -> Track:
        client = self._require_client()
        parsed = self.parse_url(url)
        if not parsed or parsed[0] != "track":
            raise MediaExtractionError("La URL no corresponde a una cancion de Spotify.")
        try:
            data = await asyncio.to_thread(client.track, parsed[1])
        except spotipy.SpotifyException as exc:
            raise MediaExtractionError("No pude consultar esa cancion en Spotify.") from exc
        return self._to_track(data, requester)

    async def resolve_playlist(
        self, url: str, requester: Requester, *, limit: int = 100
    ) -> list[Track]:
        client = self._require_client()
        parsed = self.parse_url(url)
        if not parsed or parsed[0] != "playlist":
            raise MediaExtractionError("La URL no corresponde a una playlist de Spotify.")

        try:
            page = await asyncio.to_thread(
                client.playlist_items,
                parsed[1],
                fields="items(track(id,name,duration_ms,external_urls,artists,album(images))),next",
                additional_types=("track",),
                limit=min(limit, 100),
            )
            items: list[Mapping[str, Any]] = list(page.get("items", []))
            while page.get("next") and len(items) < limit:
                page = await asyncio.to_thread(client.next, page)
                items.extend(page.get("items", []))
        except spotipy.SpotifyException as exc:
            raise MediaExtractionError("No pude consultar esa playlist en Spotify.") from exc

        tracks = [
            self._to_track(item["track"], requester)
            for item in items[:limit]
            if item.get("track") and item["track"].get("id")
        ]
        if not tracks:
            raise MediaExtractionError("La playlist no contiene canciones disponibles.")
        return tracks

    def _require_client(self) -> spotipy.Spotify:
        if self._client is None:
            raise SpotifyNotConfiguredError(
                "Spotify no esta configurado. Completa SPOTIFY_CLIENT_ID y "
                "SPOTIFY_CLIENT_SECRET en el archivo .env."
            )
        return self._client

    @staticmethod
    def _to_track(data: Mapping[str, Any], requester: Requester) -> Track:
        artists = ", ".join(
            str(artist.get("name", "")) for artist in data.get("artists", [])
        ).strip(", ")
        title = str(data.get("name") or "Titulo desconocido")
        images = data.get("album", {}).get("images", [])
        spotify_url = data.get("external_urls", {}).get("spotify", "")
        return Track(
            title=f"{artists} - {title}" if artists else title,
            webpage_url=str(spotify_url),
            playback_query=f"{artists} - {title} audio",
            requester=requester,
            duration=int(data.get("duration_ms", 0) / 1000) or None,
            uploader=artists or "Spotify",
            thumbnail=str(images[0]["url"]) if images else None,
            source="spotify",
        )
