from discord.ext import commands
from discord import embeds
import spotifyhandler
import queuehandler
import discord
import yt_handler
import constantes
import regex
import json
import utils


queues = {}

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
        embed.add_field(name=f"🔹skip", value="Pasa a la siguiente cancion en la cola", inline=False)
        embed.add_field(name=f"🔹stop", value="Desconecta al bot", inline=False)
        embed.add_field(name=f"🔹clear", value="Limpia la cola en caso de que hayan problemas", inline=False)

        embed.set_footer(text=f"Usa el prefijo {constantes.BOT_PREFIX} para los comandos de texto.")

        await ctx.send(embed=embed)

    @bot.command(name="ping")
    async def ping_command(ctx):
        await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

    @bot.command(name="playlist")
    async def playlist(ctx, arg):
        if ctx.author.voice is None:
            await ctx.send("Necesitas estar en un canal de voz para usar este comando")
            return
        voice_channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await voice_channel.connect()
        else:
            await ctx.voice_client.move_to(voice_channel)
        await ctx.message.add_reaction("✅")

    @bot.command(name="stop", aliases=["pausar", "detener", "disconnect"])
    async def stop_music(ctx):
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
            # Utilizar la función stop() de la clase QueueHandler
            guild_id = ctx.guild.id
            if guild_id not in queues:
                await ctx.send("No hay canciones en la cola.")
                return
            queue = queues[guild_id]
            queue.stop()
            await ctx.voice_client.disconnect()
            await ctx.message.add_reaction("👋")
        except Exception as e:
            await ctx.send(f"Error al desconectar: {e}")

    @bot.command(name="play",aliases=["reproducir"])
    async def play_music(ctx, *, arg=None):
        # Si no se proporciona un argumento, se envía un mensaje de error
        if arg is None:
            await ctx.send("Por favor, proporciona una canción o URL para reproducir.")
            return

        # Instancia la query con el argumento proporcionado
        query = "ytsearch:" + arg

        # Si el argumento es una URL de Spotify, se modifica la query para llenarla con los datos proporiconados por el scrappy de spotify
        # Se utiliza el regex para validar si es una URL de Spotify
        if regex.match(constantes.SPOTIFY_REGEX, arg):
            ctx.send("URL de Spotify detectada, obteniendo datos...")
            datos = spotifyhandler.obterner_datos_url_spotify(arg)
            if datos is None:
                await ctx.send("No se pudo obtener la canción de Spotify.")
                return
            titulo_cancion = datos["titulo"]
            autor_cancion = datos["artista"]
            query = f"ytsearch: {titulo_cancion} {autor_cancion}"

        try:
            # Declarar la queue
            guild_id = ctx.guild.id
            if guild_id not in queues:
                queues[guild_id] = queuehandler.QueueHandler(
                    queue=[],
                    current_song=None,
                    now_playing=None,
                    loop_queue=False,
                    is_playing=False,
                    voice_channel=ctx.author.voice.channel,
                    ctx=ctx,
                )
            queue = queues[guild_id]
            queue.voice_client = ctx.voice_client or await ctx.author.voice.channel.connect()
        except Exception as e:
            await ctx.send(f"Error al conectar al canal de voz: {e}")
            return



        # Una vez obtenida la query, se procede a buscar la canción en YouTube
        try:
            resultados = await yt_handler.buscador_ytdlp_async(query, yt_handler.ytdlp_opts(playlist=False))
            canciones = resultados.get("entries", [])
            if resultados is None or len(canciones) == 0:
                await ctx.send("No se encontraron resultados.")
                return

            primera_cancion = canciones[0]

            # Se prepara el objeto de la canción a reproducir
            autor_cancion = primera_cancion.get("uploader", "Unknown")
            titulo_cancion = primera_cancion.get("title", "Untitled")
            thumbnail_cancion = primera_cancion.get("thumbnail", "No thumbnail")
            url_cancion = primera_cancion["original_url"]
            url_ytdlp = primera_cancion['url']
            duracion_cancion = primera_cancion.get("duration", 0)
            requester = ctx.author.name
            cancion = queuehandler.Cancion(
                nombrecancion=titulo_cancion,
                uploadercancion=autor_cancion,
                thumbnail=thumbnail_cancion,
                urlcancion=url_cancion,
                urlytdlp=url_ytdlp,
                duration=duracion_cancion,
                requester=requester,
            )
            queue.add_cancion(cancion)
            await ctx.send(f"Se ha añadido la canción a la cola: {cancion}")
            await ctx.message.add_reaction("✅")

        except yt_handler.YTError as e:
            await ctx.send(f"Error al buscar la canción: {e}")



        # ffmpeg_opts = {
        #     "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        #     "options": "-vn",
        # }

        # if ctx.author.voice is None:
        #     await ctx.message.add_reaction("❌")
        #     await ctx.send("Necesitas estar en un canal de voz para usar este comando")
        #     return

        # voice_channel = ctx.author.voice.channel
        # if ctx.voice_client is None:
        #     await voice_channel.connect()

        # fuente = discord.FFmpegPCMAudio(url_ytdlp, **ffmpeg_opts)
        # voice_client = ctx.voice_client or await voice_channel.connect()
        # voice_client.play(fuente, after=lambda e: print(f"Error al reproducir: {e}") if e else None)

        # await ctx.message.add_reaction("✅")
        # await ctx.send(f"Reproduciendo: {cancion}")

    @bot.command(name="skip", aliases=["saltar"])
    async def skip_music(ctx):
        """
        Salta la canción actual y reproduce la siguiente en la cola.
        Usando de base la clase de QueueHandler, debe llamar a la funcion play_next()
        """
        guild_id = ctx.guild.id
        if guild_id not in queues:
            await ctx.send("No hay canciones en la cola.")
            return
        queue = queues[guild_id]
        if queue.is_playing:
            queue.voice_client.stop()
            await queue.play_next()
            await ctx.message.add_reaction("✅")
        else:
            await ctx.send("No hay canciones en la cola.")

    @bot.command(name="queue", aliases=["lista", "cola"])
    async def queue_music(ctx):
        """
        Muestra la lista de canciones en la cola.
        Usando de base la clase de QueueHandler, debe llamar a la funcion get_queue()
        """
        guild_id = ctx.guild.id
        if guild_id not in queues:
            await ctx.send("No hay canciones en la cola.")
            return
        queue = queues[guild_id]
        if len(queue.queue) == 0:
            await ctx.send("No hay canciones en la cola.")
            return
        queue_list = "\n".join([str(cancion) for cancion in queue.queue])
        await ctx.send(f"Lista de canciones en la cola:\n{queue_list}")
        await ctx.message.add_reaction("✅")

    @bot.command(name="clear", aliases=["limpiar"])
    async def clear_queue(ctx):
        """
        Limpia la cola de canciones.
        Usando de base la clase de QueueHandler, debe llamar a la funcion stop()
        """
        guild_id = ctx.guild.id
        if guild_id not in queues:
            await ctx.send("No hay canciones en la cola.")
            return
        queue = queues[guild_id]
        queue.stop()
        await ctx.send("Cola de canciones limpiada.")