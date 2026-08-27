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

    def get_tracks(self, url: str) -> list[str]:
        if not self.sp:
            return []

        search_queries = []
        if "track" in url:
            track = self.sp.track(url)
            search_queries.append(f"{track['name']} {track['artists'][0]['name']}")
        elif "playlist" in url:
            results = self.sp.playlist_items(url)
            for item in results.get('items', []):
                track = item.get('track')
                if track:
                    search_queries.append(f"{track['name']} {track['artists'][0]['name']}")
        return search_queries
