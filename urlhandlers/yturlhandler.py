from ytmusicapi import YTMusic
import json

ytmusic = YTMusic()

url = "https://www.youtube.com/watch?v=a46Pu9-QIto"

def obtener_datos_url_ytmusic(url: str):
    """
    Obtiene los datos de una canción de YT Music a partir de su URL.
    """
    video_id = url.split("v=")[-1].split("&")[0]
    search_results = ytmusic.get_song(videoId=video_id)

    if search_results is None:
        return None

    with open("ytmusic_data.json", "w") as f:
        json.dump(search_results, f, indent=4)
    datos = {
        "titulo": search_results["videoDetails"]["title"],
        "artista": search_results["videoDetails"]["author"],
        "url": url
    }
    return datos

print(obtener_datos_url_ytmusic(url))