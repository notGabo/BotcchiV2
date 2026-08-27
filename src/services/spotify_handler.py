import re
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from src.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET


class SpotifyHandler:
    def __init__(self):
        self.sp = None
        if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
            auth_manager = SpotifyClientCredentials(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager)

    def is_spotify_url(self, url: str) -> bool:
        return "open.spotify.com" in url

    def extract_spotify_id(self, url: str) -> tuple[str | None, str | None]:
        """Extrae el tipo (track, playlist, album) y el ID limpio eliminando parámetros de URL."""
        match = re.search(r'open\.spotify\.com/(track|playlist|album)/([a-zA-Z0-9]+)', url)
        if match:
            return match.group(1), match.group(2)
        return None, None

    def get_tracks(self, url: str) -> list[str]:
        """Obtiene la lista de términos de búsqueda ("Título Artista") para YouTube."""
        if not self.sp:
            print("[SpotifyHandler] Error: SPOTIFY_CLIENT_ID o SPOTIFY_CLIENT_SECRET no configurados.")
            return []

        item_type, item_id = self.extract_spotify_id(url)
        if not item_type or not item_id:
            print(f"[SpotifyHandler] No se pudo obtener el ID válido desde la URL: {url}")
            return []

        search_queries = []
        try:
            if item_type == "track":
                track = self.sp.track(item_id)
                if track and 'name' in track:
                    artists = ", ".join([artist['name'] for artist in track.get('artists', []) if 'name' in artist])
                    search_queries.append(f"{track['name']} {artists}")

            elif item_type == "playlist":
                results = self.sp.playlist_items(item_id)
                while results:
                    for item in results.get('items', []):
                        if not item:
                            continue
                        track = item.get('track')
                        if track and track.get('name') and track.get('type') == 'track':
                            artists = ", ".join([artist['name'] for artist in track.get('artists', []) if 'name' in artist])
                            search_queries.append(f"{track['name']} {artists}")
                    results = self.sp.next(results) if results.get('next') else None

            elif item_type == "album":
                results = self.sp.album_tracks(item_id)
                while results:
                    for item in results.get('items', []):
                        if item and item.get('name'):
                            artists = ", ".join([artist['name'] for artist in item.get('artists', []) if 'name' in artist])
                            search_queries.append(f"{item['name']} {artists}")
                    results = self.sp.next(results) if results.get('next') else None

        except Exception as exc:
            print(f"[SpotifyHandler] Error consultando Spotify API ({item_type} ID: {item_id}): {exc}")

        return search_queries