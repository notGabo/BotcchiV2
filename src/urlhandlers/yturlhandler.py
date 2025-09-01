from ytmusicapi import YTMusic
import json
import re


ytmusic = YTMusic()

def validar_url_playlist_youtube(url: str) -> bool:
    """
    Valida si la URL proporcionada es una playlist de YouTube.
    """
    patron = r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.*(list=)([a-zA-Z0-9_-]+)'
    return re.match(patron, url) is not None

def obtener_datos_playlist_youtube(url: str):
    """
    Obtiene los datos de una playlist de YouTube a partir de su URL.
    """
    if re.match(r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.*(list=)([a-zA-Z0-9_-]+)', url):
        playlist_id = re.search(r'list=([a-zA-Z0-9_-]+)', url).group(1)
    playlistinfo = ytmusic.get_playlist(playlist_id, limit=100)
    canciones = playlistinfo['tracks']
    listadatos = []
    for cancion in canciones:
        objetocancion = {
            "titulo": cancion['title'],
            "artista": cancion['artists'][0]['name'],
            "url": f"https://www.youtube.com/watch?v={cancion['videoId']}"
        }
        listadatos.append(objetocancion)
    return listadatos

def obtener_datos_url_ytmusic(url: str):
    """
    Obtiene los datos de una canción de YT Music a partir de su URL.
    """
    video_id = url.split("v=")[-1].split("&")[0]
    search_results = ytmusic.get_song(videoId=video_id)

    if search_results is None:
        return None
    datos = {
        "titulo": search_results["videoDetails"]["title"],
        "artista": search_results["videoDetails"]["author"],
        "url": url
    }
    return datos


# url = "https://www.youtube.com/watch?v=n1q-R6iNxRE&list=PLFNlH5nxEUMH1eegyXy5SVeXYuDRBA6cf"
# obtener_datos_playlist_youtube(url)
