import re
import json
import aiohttp
from urllib.parse import quote

class LyricsHandler:
    PALABRAS_EXCLUIR = [
        "】", "【", "mv", "【FULL MV】", "upgrade", "topic", "official", "video", 
        "audio", "official video", "official audio", "official music", 
        "(official music video)", "(official audio)", "(official music)", 
        "lyric", "music", "lyrics", "feat.", "ft.", "ft", "feat", "remix", 
        "version", "live", "hd", "4k", "(lyrics)", "(lyric)", "(official video)", 
        "(official audio)", "(oficial video)", "()", "(", ")", "[]", "[", "]"
    ]

    @classmethod
    def limpiar_texto(cls, texto: str) -> str:
        """Limpia caracteres y términos basura de la consulta."""
        texto_limpio = texto.lower()
        for palabra in cls.PALABRAS_EXCLUIR:
            texto_limpio = texto_limpio.replace(palabra.lower(), "")
        
        texto_limpio = re.sub(r'\(.*?\)', '', texto_limpio)
        texto_limpio = re.sub(r'[\-\_]', ' ', texto_limpio)
        texto_limpio = re.sub(r'\s+', ' ', texto_limpio).strip()
        return texto_limpio

    @classmethod
    async def buscar_en_letras_com(cls, query: str) -> dict | None:
        """Intento 1: Scraping en Letras.com mediante Solr."""
        query_limpia = cls.limpiar_texto(query)
        busqueda_encoded = quote(query_limpia)
        solr_url = f"https://solr.sscdn.co/letras/m1/?q={busqueda_encoded}&wt=json&rows=10"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                async with session.get(solr_url, timeout=10) as resp:
                    if resp.status != 200:
                        return None
                    raw_text = await resp.text()
                    json_str = raw_text[10:-2]
                    datos = json.loads(json_str)
                    docs = datos.get('response', {}).get('docs', [])

                    if not docs:
                        return None

                    candidato = docs[0]
                    artista = candidato.get('art', 'Desconocido')
                    titulo = candidato.get('txt', query_limpia)
                    url_path = candidato.get('url')

                    if not url_path:
                        return None

                url_artist = artista.replace(" ", "-").lower()
                song_url = f"https://www.letras.com/{url_artist}/{url_path}/"

                async with session.get(song_url, timeout=10) as resp:
                    if resp.status != 200:
                        return None
                    html = await resp.text()

                patron = r'<div class="lyric-original">(.*?)</div>'
                coincidencia = re.search(patron, html, re.DOTALL)
                if not coincidencia:
                    return None

                contenido = coincidencia.group(1)
                letra = re.sub(r'<p>', '\n\n', contenido)
                letra = re.sub(r'</p>', '', letra)
                letra = re.sub(r'<br\s*/?>', '\n', letra)
                letra = re.sub(r'<.*?>', '', letra)
                letra = re.sub(r'&#39;', "'", letra)
                letra = re.sub(r'&quot;', '"', letra)
                letra = re.sub(r'&amp;', '&', letra)
                letra = re.sub(r'&lt;', '<', letra)
                letra = re.sub(r'&gt;', '>', letra)
                letra = re.sub(r'\n{3,}', '\n\n', letra).strip()

                return {
                    "artist": artista.title(),
                    "title": titulo.title(),
                    "lyrics": letra,
                    "source": "Letras.com"
                }
            except Exception as e:
                print(f"[LyricsHandler] Error en Letras.com: {e}")
                return None

    @classmethod
    async def get_lyrics(cls, query: str) -> dict | None:
        """Punto de entrada principal con estrategia de Fallback."""
        # 1. Primer intento en Letras.com
        resultado = await cls.buscar_en_letras_com(query)
        if resultado:
            return resultado

        # 2. Respaldo (Fallback) en LRCLIB API si el primero falla o da None
        query_limpia = cls.limpiar_texto(query)
        url = f"https://lrclib.net/api/search?q={quote(query_limpia)}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        results = await resp.json()
                        for item in results:
                            lyrics = item.get("plainLyrics") or item.get("syncedLyrics")
                            if lyrics:
                                return {
                                    "artist": item.get("artistName", "Desconocido").title(),
                                    "title": item.get("trackName", query_limpia).title(),
                                    "lyrics": lyrics,
                                    "source": "LRCLIB API"
                                }
        except Exception as e:
            print(f"[LyricsHandler] Error en LRCLIB: {e}")

        return None