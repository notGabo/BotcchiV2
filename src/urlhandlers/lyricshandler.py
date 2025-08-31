import requests
import json
import re

endpointBusqueda = "https://solr.sscdn.co/letras/m1/?q={}&wt=json&rows=10"

def limpieza_string(artista, cancion):
    palabras_excluir = ["topic","official", "video", "audio","official video","official audio","official music", "(official music video)","(official audio)","(official music)", "(official music video)" "lyric","music" ,"lyrics", "feat.", "ft.", "ft", "feat", "remix", "version", "live", "hd", "4k","(lyrics)","(lyric)","(official video)","(official audio)","(oficial video)","(official audio)","()","(",")","[]","[","]"]

    cancion = cancion.lower()
    artista = artista.lower()

    if artista in cancion:
        cancion = cancion.replace(artista, "").strip()

    cancion = cancion.replace("-", "").strip()

    for palabra in palabras_excluir:
        cancion = cancion.replace(palabra.lower(), "").strip()

    cancion = re.sub(r'\(.*?\)', '', cancion).strip()

    cancion = re.sub(r'\s+', ' ', cancion).strip().title()
    artista = re.sub(r'\s+', ' ', artista).strip().title()

    return artista, cancion

def BuscarObjetoCancion(artista, cancion):
    try:
        busqueda = f"{artista} {cancion}"
        busqueda = requests.utils.quote(busqueda)
        urlBusqueda = endpointBusqueda.format(busqueda)
        respuesta = requests.get(urlBusqueda, timeout=10)
        if respuesta.status_code != 200:
            raise Exception(f"Error en la solicitud: {respuesta.status_code}")
        datos = json.loads(respuesta.text[10:-2])
        return datos['response']['docs']
    except Exception as e:
        print(f"Error al buscar la letra: {e}")
        return None

def GenerarObjetoCancion(artista, cancion):
    try:
        busqueda = f"{artista} {cancion}"
        busqueda = requests.utils.quote(busqueda)
        urlBusqueda = endpointBusqueda.format(busqueda)
        print(f"URL de búsqueda: {urlBusqueda}")
        respuesta = requests.get(urlBusqueda, timeout=10)
        if respuesta.status_code != 200:
            raise Exception(f"Error en la solicitud: {respuesta.status_code}")
        datos = json.loads(respuesta.text[10:-2])
        # Escojer el mejor candidato de la lista de resultados
        for resultado in datos['response']['docs']:
            titulo_resultado_lowercase = resultado.get('art', '').lower()
            artista_resultado_lowercase = resultado.get('txt', '').lower()
            cancion_lowercase = cancion.lower()
            artista_lowercase = artista.lower()
            if (cancion_lowercase in artista_resultado_lowercase and artista_lowercase in titulo_resultado_lowercase) or (cancion_lowercase in titulo_resultado_lowercase and artista_lowercase in artista_resultado_lowercase):
                print(f"Resultado encontrado: {resultado}")
                return resultado
        return None
    except Exception as e:
        print(f"Error al buscar la letra: {e}")
        return None

def GenerarLinkCancion(objeto):
    if objeto.get('url', False):
        url_artist = objeto["art"].replace(" ", "-").lower()
        print(f"Generated URL: https://www.letras.com/{url_artist}/{objeto['url']}/")
        return f"https://www.letras.com/{url_artist}/{objeto['url']}/"
    return None

def GenerarLetraCancion(link):
    try:
        respuesta = requests.get(link, timeout=10)
        if respuesta.status_code != 200:
            raise Exception(f"Error en la solicitud: {respuesta.status_code}")
        patron = r'<div class="lyric-original">(.*?)</div>'
        coincidencia = re.search(patron, respuesta.text, re.DOTALL)
        if coincidencia:
            contenido_crudo = coincidencia.group(1)
            letra = re.sub(r'<p>', '\n\n', contenido_crudo)
            letra = re.sub(r'</p>', '', letra)
            letra = re.sub(r'<br\s*/?>', '\n', letra)
            letra = re.sub(r'<.*?>', '', letra)
            letra = re.sub(r'&#39;', "'", letra)
            letra = re.sub(r'&quot;', '"', letra)
            letra = re.sub(r'&amp;', '&', letra)
            letra = re.sub(r'&lt;', '<', letra)
            letra = re.sub(r'&gt;', '>', letra)
            letra = re.sub(r'\n{3,}', '\n\n', letra)
            letra = letra.strip()
            return letra
        else:
            print("No se encontró la letra en la página.")
            return None
    except Exception as e:
        print(f"Error al obtener la letra: {e}")
        return None
