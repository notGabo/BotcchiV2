import discord
from discord.ext import commands
import os
from src.config import BOT_SERVIDORES_MANTENER_CONECTADO
from src.services.yt_handler import YTDLSource
from src.services.spotify_handler import SpotifyHandler
from src.services.lyrics_handler import LyricsHandler
from src.utils.embed_builder import EmbedBuilder
import asyncio


class MusicState:
    def __init__(self):
        self.queue = []
        self.current = None
        self.loading = False


FFMPEG_OPTIONS = {
    'options': '-vn'
}


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.states = {}
        self.spotify = SpotifyHandler()

    def should_keep_connected(self, guild_id):
        if not BOT_SERVIDORES_MANTENER_CONECTADO:
            return True
        return guild_id in BOT_SERVIDORES_MANTENER_CONECTADO

    def is_youtube_playlist_url(self, url):
        return "list=" in url or "playlist" in url

    async def resolve_inputs(self, source):
        if self.spotify.is_spotify_url(source):
            return self.spotify.get_tracks(source)
        if self.is_youtube_playlist_url(source):
            return await YTDLSource.extract_playlist(source)
        return [source]

    async def enqueue_resolved_tracks(self, ctx, tracks, status_title, status_message):
        if not tracks:
            raise RuntimeError("No se encontraron canciones válidas en la fuente proporcionada.")

        status_msg = await ctx.send(embed=EmbedBuilder.info(status_title, status_message))
        state = self.get_state(ctx.guild.id)
        total_tracks = len(tracks)
        state.loading = True

        try:
            first_track = tracks[0]
            first_info = None
            try:
                first_info = await YTDLSource.extract_info(first_track)
                state.queue.append({'info': first_info, 'requester': ctx.author.name, 'source': first_track, 'retry_count': 0})
                if not ctx.voice_client.is_playing() and not state.current:
                    await self.play_next(ctx)
            except Exception as exc:
                print(f"[Music] Error al procesar primera canción: {exc}")

            if total_tracks == 1 and first_info is None:
                raise RuntimeError("No se pudo obtener la canción solicitada.")

            if total_tracks > 1:
                await status_msg.edit(
                    embed=EmbedBuilder.info(
                        "Procesando contenido",
                        f"Procesando {total_tracks - 1} canciones restantes..."
                    )
                )

                semaphore = asyncio.Semaphore(5)

                async def fetch_track(track):
                    async with semaphore:
                        try:
                            info = await YTDLSource.extract_info(track)
                            return {'info': info, 'requester': ctx.author.name, 'source': track, 'retry_count': 0}
                        except Exception as exc:
                            print(f"[Music] Error procesando canción en lote ({track}): {exc}")
                            return None

                results = await asyncio.gather(*(fetch_track(t) for t in tracks[1:]))
                valid_items = [item for item in results if item is not None]
                state.queue.extend(valid_items)

                if first_info is None and not valid_items:
                    raise RuntimeError("No se pudo obtener ninguna canción válida de la fuente proporcionada.")

                added_count = len(valid_items) + (1 if first_info is not None else 0)
            else:
                added_count = 1 if first_info is not None else 0

            await status_msg.edit(
                embed=EmbedBuilder.info(
                    "Contenido cargado",
                    f"Se añadieron exitosamente **{added_count}** de **{total_tracks}** canciones a la cola."
                )
            )

        finally:
            state.loading = False

    def get_state(self, guild_id):
        if guild_id not in self.states:
            self.states[guild_id] = MusicState()
        return self.states[guild_id]

    async def play_next(self, ctx, announce: bool = True):
        state = self.get_state(ctx.guild.id)

        # 1. Validar que el bot siga efectivamente conectado al canal de voz
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            state.current = None
            return

        if state.loading and not state.queue:
            return

        # 2. Evitar dobles reproducciones simultáneas por condiciones de carrera
        if ctx.voice_client.is_playing():
            return

        if state.queue:
            state.current = state.queue.pop(0)
            await self.play_current_item(ctx, state.current, announce=announce)
        else:
            state.current = None
            if ctx.voice_client and ctx.voice_client.is_connected() and not self.should_keep_connected(ctx.guild.id):
                await ctx.voice_client.disconnect()

    async def play_current_item(self, ctx, item, announce: bool = True):
        source = item['info'].get('webpage_url') or item.get('source') or item['info'].get('url')
        if not source:
            print("[Music] No se encontró una fuente válida para reproducir.")
            asyncio.run_coroutine_threadsafe(self.play_next(ctx, announce=False), self.bot.loop)
            return

        if item.get('file_path'):
            try:
                os.remove(item['file_path'])
            except OSError:
                pass

        try:
            item['file_path'] = await YTDLSource.download_audio_file(source)
            audio_source = discord.FFmpegPCMAudio(item['file_path'], options=FFMPEG_OPTIONS['options'])
        except Exception as exc:
            print(f"[Music] No se pudo crear la fuente de audio: {exc}")
            asyncio.run_coroutine_threadsafe(self.play_next(ctx, announce=False), self.bot.loop)
            return

        def cleanup_current_file():
            file_path = item.pop('file_path', None)
            if file_path:
                try:
                    os.remove(file_path)
                except OSError:
                    pass

        def after_playing(error):
            cleanup_current_file()

            if error:
                print(f"[Music] Error en reproducción de FFmpeg: {error}")

                retry_count = item.get('retry_count', 0)
                if retry_count < 1:
                    item['retry_count'] = retry_count + 1

                    async def retry_current():
                        try:
                            retry_source = item['info'].get('webpage_url') or source
                            if retry_source:
                                item['info'] = await YTDLSource.extract_info(retry_source)
                                await self.play_current_item(ctx, item, announce=False)
                                return
                        except Exception as retry_exc:
                            print(f"[Music] Reintento de reproducción falló: {retry_exc}")

                        await self.play_next(ctx, announce=False)

                    asyncio.run_coroutine_threadsafe(retry_current(), self.bot.loop)
                    return

            asyncio.run_coroutine_threadsafe(self.play_next(ctx, announce=False), self.bot.loop)

        ctx.voice_client.play(audio_source, after=after_playing)

        if announce:
            embed = EmbedBuilder.now_playing(item['info'], item['requester'])
            content_text = (f"Se está reproduciendo: {item['info']['title']} - "
                            f"{item['info']['uploader']} ({item['info']['duration_str']})")
            await ctx.send(content=content_text, embed=embed)

    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx, *, query: str):
        if not ctx.author.voice:
            return await ctx.send(embed=EmbedBuilder.error("Debes estar en un canal de voz."))

        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        try:
            async with ctx.typing():
                if self.spotify.is_spotify_url(query) or self.is_youtube_playlist_url(query):
                    tracks = await self.resolve_inputs(query)
                    await self.enqueue_resolved_tracks(
                        ctx,
                        tracks,
                        "Cargando contenido",
                        "Obteniendo las canciones de la fuente proporcionada..."
                    )
                    return

                info = await YTDLSource.extract_info(query)
                state = self.get_state(ctx.guild.id)
                item = {'info': info, 'requester': ctx.author.name, 'source': query, 'retry_count': 0}
                state.queue.append(item)

                if not ctx.voice_client.is_playing() and not state.current:
                    await self.play_next(ctx)
                else:
                    embed = EmbedBuilder.info(
                        "Añadido a la cola",
                        f"**{info['title']}** ({info['duration_str']})"
                    )
                    await ctx.send(embed=embed)

        except Exception as exc:
            await ctx.send(embed=EmbedBuilder.error(f"Error al reproducir la canción: {exc}"))


    @commands.command(name="playlist")
    async def playlist(self, ctx, url: str):
        if not ctx.author.voice:
            return await ctx.send(embed=EmbedBuilder.error("Debes estar en un canal de voz."))

        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        try:
            async with ctx.typing():
                tracks = await self.resolve_inputs(url)
                await self.enqueue_resolved_tracks(
                    ctx,
                    tracks,
                    "Cargando Playlist",
                    "Obteniendo la lista de canciones..."
                )

        except RuntimeError as exc:
            await ctx.send(embed=EmbedBuilder.error(str(exc)))
        except Exception as exc:
            await ctx.send(embed=EmbedBuilder.error(f"Error al cargar la playlist: {exc}"))

    @commands.command(name="skip")
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send(embed=EmbedBuilder.info("Skip", "Canción saltada."))
        else:
            await ctx.send(embed=EmbedBuilder.error("No hay nada reproduciéndose."))

    @commands.command(name="stop")
    async def stop(self, ctx):
        if ctx.voice_client:
            state = self.get_state(ctx.guild.id)
            state.queue.clear()
            state.current = None
            await ctx.voice_client.disconnect()
            await ctx.send(embed=EmbedBuilder.info("Desconectado", "Bot desconectado del canal de voz."))

    @commands.command(name="clear")
    async def clear(self, ctx):
        state = self.get_state(ctx.guild.id)
        state.queue.clear()
        await ctx.send(embed=EmbedBuilder.info("Cola limpiada", "Se han eliminado todas las canciones de la cola."))

    @commands.command(name="queue", aliases=["q"])
    async def queue(self, ctx):
        state = self.get_state(ctx.guild.id)
        
        if not state.current and not state.queue:
            return await ctx.send(
                embed=EmbedBuilder.info("Cola de reproducción", "No hay ninguna canción reproduciéndose ni en la cola.")
            )

        embed = EmbedBuilder.queue(state.current, state.queue)
        await ctx.send(embed=embed)

    @commands.command(name="np")
    async def np(self, ctx):
        state = self.get_state(ctx.guild.id)
        if state.current:
            embed = EmbedBuilder.now_playing(state.current['info'], state.current['requester'])
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=EmbedBuilder.error("No hay ninguna canción reproduciéndose."))

    @commands.command(name="lyrics")
    async def lyrics(self, ctx, *, query: str = None):
        state = self.get_state(ctx.guild.id)
        
        # 1. Determinar el término de búsqueda
        search_query = query
        if not search_query:
            if state.current and state.current.get('info'):
                search_query = state.current['info']['title']
            else:
                return await ctx.send(
                    embed=EmbedBuilder.error("No hay ninguna canción reproduciéndose ni especificaste una búsqueda.")
                )

        async with ctx.typing():
            result = await LyricsHandler.get_lyrics(search_query)

            if not result:
                return await ctx.send(
                    embed=EmbedBuilder.error(f"No se encontró la letra para **{search_query}**.")
                )

            lyrics_text = result['lyrics']
            if len(lyrics_text) > 4000:
                lyrics_text = lyrics_text[:3997] + "..."

            embed = discord.Embed(
                title=f"🎵 Letra: {result['artist']} - {result['title']}",
                description=lyrics_text,
                color=discord.Color.purple()
            )
            embed.set_footer(text=f"Fuente: {result['source']}")
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Music(bot))
