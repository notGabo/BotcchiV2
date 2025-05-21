from discord.ext import commands
from discord import embeds
import discord
import yt_handler
import constantes
import regex
import utils

# Comandos bot
async def setup(bot):
    @bot.command(name="comandos", aliases=["ayuda","","help"])
    async def list_commands(ctx):
        embed = embeds.Embed(
            title="Comandos disponibles",
            description="Aquí tienes una lista de los comandos disponibles:",
            color=0x00ff00
        )

        embed.add_field(name=f"🔹comandos", value="Muestra este mensaje", inline=False)
        embed.add_field(name=f"🔹ping", value="Responde con 'Pong!'", inline=False)
        embed.add_field(name=f"🔹play [canción o url]", value="Reproduce una canción", inline=False)
        embed.add_field(name=f"🔹stop", value="Desconecta al bot", inline=False)

        embed.set_footer(text=f"Usa el prefijo {constantes.BOT_PREFIX} para los comandos de texto.")

        await ctx.send(embed=embed)

    @bot.command(name="ping")
    async def ping_command(ctx):
        await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

    @bot.command(name="playlist")
    async def playlist(ctx, arg):
        """
        Reproduce una lista de reproducción en el canal de voz actual, tomando la URL de la lista de reproducción.
        y todas sus canciones metiendolkas en la cola.
        Si el bot no está conectado a un canal de voz, se conecta al canal de voz del usuario.
        """
        if ctx.author.voice is None:
            await ctx.send("Necesitas estar en un canal de voz para usar este comando")
            return
        voice_channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await voice_channel.connect()
        else:
            await ctx.voice_client.move_to(voice_channel)
        await ctx.message.add_reaction("✅")

    @bot.command(name="play",aliases=["reproducir"])
    async def play_music(ctx, *, arg=None):
        """
        Reproduce una canción en el canal de voz actual.
        Si el bot no está conectado a un canal de voz, se conecta al canal de voz del usuario.
        Si se añade una canción a la cola, se reproduce la siguiente canción en la cola.
        """
        if arg is None:
            await ctx.send("Por favor, proporciona una canción o URL para reproducir.")
            return

        # comprobar si es una url de spotify
        if regex.match(constantes.SPOTIFY_REGEX, arg):
            await ctx.send("No se puede reproducir canciones de Spotify.")
            return

        query = "ytsearch:" + arg
        try:
            resultados = await yt_handler.buscador_ytdlp_async(query, yt_handler.ytdlp_opts(playlist=False))
            canciones = resultados.get("entries", [])
            if resultados is None or len(canciones) == 0:
                await ctx.send("No se encontraron resultados.")
                return
            primera_cancion = canciones[0]
            url_cancion = primera_cancion["url"]
            titulo_cancion = primera_cancion.get("title", "Untitled")
            autor_cancion = primera_cancion.get("uploader", "Unknown")
        except yt_handler.YTError as e:
            await ctx.send(f"Error al buscar la canción: {e}")

        print(f"Título de la canción: {titulo_cancion} - Autor: {autor_cancion}")
        print(f"URL de la canción: {url_cancion}")

        ffmpeg_opts = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn",
        }


        if ctx.author.voice is None:
            await ctx.message.add_reaction("❌")
            await ctx.send("Necesitas estar en un canal de voz para usar este comando")
            return

        voice_channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await voice_channel.connect()

        fuente = discord.FFmpegPCMAudio(url_cancion, **ffmpeg_opts)
        voice_client = ctx.voice_client or await voice_channel.connect()
        voice_client.play(fuente, after=lambda e: print(f"Error al reproducir: {e}") if e else None)

        await ctx.message.add_reaction("✅")
        await ctx.send(f"Reproduciendo: {autor_cancion} - {titulo_cancion}")
    @bot.command(name="stop", aliases=["pausar", "detener", "disconnect"])
    async def stop_music(ctx):
        """Desconecta al bot del canal de voz actual."""
        if ctx.voice_client is None:
            await ctx.send("No estoy conectado a ningún canal de voz.")
            await ctx.message.add_reaction("❓")
            return
        if ctx.author.voice is None:
            await ctx.send("Necesitas estar en un canal de voz para usar este comando.")
            await ctx.message.add_reaction("❓")
            return
        if ctx.author.voice.channel != ctx.voice_client.channel:
            await ctx.send("No estás en el mismo canal de voz que yo.")
            await ctx.message.add_reaction("❗")
            return
        try:
            await ctx.voice_client.disconnect()
            await ctx.message.add_reaction("👋")
        except Exception as e:
            await ctx.send(f"Error al desconectar: {e}")