import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from os import getenv
from dotenv import load_dotenv

load_dotenv()

SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET")

auth_manager = SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
)
sp = spotipy.Spotify(auth_manager=auth_manager)


def obtener_datos_url_spotify(url):
    """
    Obtiene los datos de una canción de Spotify a partir de su URL.
    """
    try:
        track = sp.track(url)
        return {
            "titulo": track["name"],
            "artista": track["artists"][0]["name"],
            "url": track["external_urls"]["spotify"]
        }
    except Exception as e:
        print(f"Error al obtener datos de Spotify: {e}")
        return None