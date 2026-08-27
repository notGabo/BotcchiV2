import discord
from discord.ext import commands
from src.services.yt_handler import YTDLSource
from src.services.spotify_handler import SpotifyHandler
from src.services.lyrics_handler import LyricsHandler
from src.utils.embed_builder import EmbedBuilder


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

    @commands.command(name="play")
    async def play(self, ctx, *, query: str):
        if not ctx.author.voice:
            return await ctx.send(embed=EmbedBuilder.error("Debes estar en un canal de voz."))

        # Conectar al canal si no está conectado
        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        try:
            async with ctx.typing():
                info = await YTDLSource.extract_info(query)
                state = self.get_state(ctx.guild.id)
                item = {'info': info, 'requester': ctx.author.name}

                # Añadir siempre el item a la cola primero
                state.queue.append(item)

                if ctx.voice_client.is_playing() or state.current:
                    content_text = (f"Se ha añadido la canción a la cola: {info['title']} - "
                                    f"{info['uploader']} ({info['duration_str']})")
                    embed = EmbedBuilder.now_playing(info, ctx.author.name)
                    await ctx.send(content=content_text, embed=embed)
                else:
                    await self.play_next(ctx)
        except RuntimeError as exc:
            await ctx.send(embed=EmbedBuilder.error(str(exc)))

    @commands.command(name="playlist")
    async def playlist(self, ctx, url: str):
        if not ctx.author.voice:
            return await ctx.send(embed=EmbedBuilder.error("Debes estar en un canal de voz."))

        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        try:
            async with ctx.typing():
                tracks = []
                if self.spotify.is_spotify_url(url):
                    tracks = self.spotify.get_tracks(url)
                else:
                    tracks = [url]

                state = self.get_state(ctx.guild.id)
                successfully_added = 0
                for track in tracks:
                    try:
                        info = await YTDLSource.extract_info(track)
                        state.queue.append({'info': info, 'requester': ctx.author.name})
                        successfully_added += 1
                    except RuntimeError as exc:
                        await ctx.send(embed=EmbedBuilder.error(f"No se pudo añadir una canción: {track}\n{exc}"))

                await ctx.send(embed=EmbedBuilder.info("Playlist Cargada", f"Se añadieron {successfully_added} canciones a la cola."))
                if not ctx.voice_client.is_playing() and not state.current and successfully_added:
                    await self.play_next(ctx)
        except RuntimeError as exc:
            await ctx.send(embed=EmbedBuilder.error(str(exc)))

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

    @commands.command(name="queue")
    async def queue(self, ctx):
        state = self.get_state(ctx.guild.id)
        if not state.queue:
            return await ctx.send(embed=EmbedBuilder.info("Cola vacía", "No hay canciones en la cola."))

        description = "".join([f"`{i+1}.` {item['info']['title']}" for i, item in enumerate(state.queue[:10])])
        await ctx.send(embed=EmbedBuilder.info("Cola de reproducción", description))

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
