import discord
from discord.ext import commands
from src.services.yt_handler import YTDLSource
from src.services.spotify_handler import SpotifyHandler
from src.services.lyrics_handler import LyricsHandler
from src.utils.embed_builder import EmbedBuilder
import asyncio


class MusicState:
    def __init__(self):
        self.queue = []
        self.current = None


FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.states = {}
        self.spotify = SpotifyHandler()

    def get_state(self, guild_id):
        if guild_id not in self.states:
            self.states[guild_id] = MusicState()
        return self.states[guild_id]

    async def play_next(self, ctx):
        state = self.get_state(ctx.guild.id)

        # 1. Validar que el bot siga efectivamente conectado al canal de voz
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            state.current = None
            return

        # 2. Evitar dobles reproducciones simultáneas por condiciones de carrera
        if ctx.voice_client.is_playing():
            return

        if state.queue:
            state.current = state.queue.pop(0)
            audio_source = discord.FFmpegPCMAudio(state.current['info']['url'], **FFMPEG_OPTIONS)

            def after_playing(error):
                if error:
                    print(f"[Music] Error en reproducción de FFmpeg: {error}")
                # Invocar el siguiente tema de forma segura en el loop del bot
                self.bot.loop.create_task(self.play_next(ctx))

            ctx.voice_client.play(audio_source, after=after_playing)

            embed = EmbedBuilder.now_playing(state.current['info'], state.current['requester'])
            content_text = (f"Se está reproduciendo: {state.current['info']['title']} - "
                            f"{state.current['info']['uploader']} ({state.current['info']['duration_str']})")
            await ctx.send(content=content_text, embed=embed)
        else:
            state.current = None

    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx, *, query: str):
        if not ctx.author.voice:
            return await ctx.send(embed=EmbedBuilder.error("Debes estar en un canal de voz."))

        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        try:
            async with ctx.typing():
                info = await YTDLSource.extract_info(query)
                state = self.get_state(ctx.guild.id)
                item = {'info': info, 'requester': ctx.author.name}
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
                status_msg = await ctx.send(
                    embed=EmbedBuilder.info("Cargando Playlist", "Obteniendo la lista de canciones...")
                )

                # 1. Obtener la lista plana de URLs / búsquedas
                tracks = []
                if self.spotify.is_spotify_url(url):
                    tracks = self.spotify.get_tracks(url)
                elif "list=" in url or "playlist" in url:
                    tracks = await YTDLSource.extract_playlist(url)
                else:
                    tracks = [url]

                if not tracks:
                    return await status_msg.edit(
                        embed=EmbedBuilder.error("No se encontraron canciones en la lista proporcionada.")
                    )

                state = self.get_state(ctx.guild.id)
                total_tracks = len(tracks)

                # 2. Procesar la primera canción inmediatamente para iniciar la música sin demora
                first_track = tracks[0]
                try:
                    first_info = await YTDLSource.extract_info(first_track)
                    state.queue.append({'info': first_info, 'requester': ctx.author.name})
                    if not ctx.voice_client.is_playing() and not state.current:
                        await self.play_next(ctx)
                except Exception as exc:
                    print(f"[Music] Error al procesar primera canción: {exc}")

                # 3. Si hay más canciones, extraer el resto en paralelo (lote de 5 a la vez)
                if total_tracks > 1:
                    await status_msg.edit(
                        embed=EmbedBuilder.info(
                            "Cargando Playlist en paralelo...",
                            f"Procesando {total_tracks - 1} canciones restantes..."
                        )
                    )

                    # Semáforo para limitar a 5 extracciones simultáneas (evita bloqueo de IP y saturación)
                    semaphore = asyncio.Semaphore(5)

                    async def fetch_track(track):
                        async with semaphore:
                            try:
                                info = await YTDLSource.extract_info(track)
                                return {'info': info, 'requester': ctx.author.name}
                            except Exception as exc:
                                print(f"[Music] Error procesando canción en playlist ({track}): {exc}")
                                return None

                    # asyncio.gather mantiene el orden exacto de la lista
                    results = await asyncio.gather(*(fetch_track(t) for t in tracks[1:]))

                    # Filtrar canciones fallidas y añadirlas a la cola en bloque
                    valid_items = [item for item in results if item is not None]
                    state.queue.extend(valid_items)

                    added_count = len(valid_items) + (1 if 'first_info' in locals() else 0)
                else:
                    added_count = 1

                await status_msg.edit(
                    embed=EmbedBuilder.info(
                        "Playlist Cargada",
                        f"Se añadieron exitosamente **{added_count}** de **{total_tracks}** canciones a la cola."
                    )
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
