from __future__ import annotations

from botcchi.models import Requester, Track
from botcchi.services.errors import MediaExtractionError
from botcchi.services.spotify import SpotifyService
from botcchi.services.youtube import YouTubeService


class MediaResolver:
    def __init__(self, youtube: YouTubeService, spotify: SpotifyService) -> None:
        self.youtube = youtube
        self.spotify = spotify

    async def resolve_track(self, query: str, requester: Requester) -> Track:
        spotify_url = self.spotify.parse_url(query)
        if spotify_url:
            if spotify_url[0] == "playlist":
                raise MediaExtractionError(
                    "Usa el comando playlist para cargar una playlist de Spotify."
                )
            return await self.spotify.resolve_track(query, requester)
        return await self.youtube.resolve_track(query, requester)

    async def resolve_playlist(self, url: str, requester: Requester) -> list[Track]:
        spotify_url = self.spotify.parse_url(url)
        if spotify_url:
            if spotify_url[0] != "playlist":
                raise MediaExtractionError(
                    "Esa URL es una cancion. Usa el comando play para reproducirla."
                )
            return await self.spotify.resolve_playlist(url, requester)
        if not url.startswith(("http://", "https://")):
            raise MediaExtractionError("Debes indicar una URL de playlist valida.")
        return await self.youtube.resolve_playlist(url, requester)
