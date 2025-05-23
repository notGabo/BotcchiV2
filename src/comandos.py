from discord.ext import commands
from discord import embeds
import src.urlhandlers.spotifyurlhandler as spotifyurlhandler
import src.urlhandlers.yturlhandler as yturlhandler
import src.queuehandler as queuehandler
import src.constantes as constantes
import src.yt_handler as yt_handler
import discord
import regex
import json
import asyncio
import utils


queues = {}
loop = asyncio.get_event_loop()

# Comandos bot
async def setup(bot):
    @bot.command(name="comandos", aliases=["ayuda","","help"])
    async def list_commands(ctx):
        embed = embeds.Embed(
            title="Comandos disponibles",
            description="Aquí tienes una lista de los comandos disponibles:",
            color=0x00ff00
        )

        embed.title = f"Comandos de {constantes.BOT_NAME}"
        embed.description = f"Hola, soy {constantes.BOT_NAME}, mi prefijo es {constantes.BOT_PREFIX}. Aquí tienes una lista de mis comandos disponibles:"
        embed.add_field(name=f"🔹comandos", value="Muestra este mensaje", inline=False)
        embed.add_field(name=f"🔹ping", value="Responde con 'Pong!'", inline=False)
        embed.add_field(name=f"🔹play [canción o url]", value="Reproduce una canción.", inline=False)
        embed.add_field(name=f"🔹playlist [url]", value="Reproduce una lista de reproducción de Spotify o Youtube.", inline=False)
        embed.add_field(name=f"🔹skip", value="Pasa a la siguiente cancion en la cola", inline=False)
        embed.add_field(name=f"🔹stop", value="Desconecta al bot", inline=False)
        embed.add_field(name=f"🔹clear", value="Limpia la cola en caso de que hayan problemas", inline=False)
        embed.add_field(name=f"🔹queue", value="Muestra la lista de canciones en la cola", inline=False)
        embed.add_field(name=f"🔹[WIP] np", value="Muestra la cancion en reproduccion", inline=False)

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
        use_direct_url = False

        # Si el argumento es una URL de Youtube, usarla directamente
        if regex.match(constantes.YT_REGEX, arg) or regex.match(constantes.YTMUSIC_REGEX, arg):
            print("URL de Youtube/YTMusic detectada, usando URL directamente...")
            query = arg
            use_direct_url = True

        # Si el argumento es una URL de Spotify, se modifica la query para buscarla en YouTube
        elif regex.match(constantes.SPOTIFY_REGEX, arg):
            print("URL de Spotify detectada, obteniendo datos...")
            datos = spotifyurlhandler.obtener_datos_url_spotify(arg)

            if datos is None:
                await ctx.send("No se pudo obtener la canción de Spotify.")
                return
            titulo_cancion = datos["titulo"]
            autor_cancion = datos["artista"]
            query = f"ytsearch: {titulo_cancion} {autor_cancion}"

        # Se instancia instancia la cola de canciones
        try:
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
                    loop=loop,
                )
            queue = queues[guild_id]
            queue.voice_client = ctx.voice_client or await ctx.author.voice.channel.connect()
        except Exception as e:
            await ctx.send(f"Error al conectar al canal de voz: {e}")
            return

        try:
            resultados = await yt_handler.buscador_ytdlp_async(query, yt_handler.ytdlp_opts(playlist=False))
             # Manejar los resultados de manera diferente si es URL directa o búsqueda
            if use_direct_url:
                primera_cancion = resultados  # Para URLs directas, el resultado está en el nivel superior
            else:
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

            # Se añade el objeto de canción a la cola
            queue.add_cancion(cancion)
            await ctx.send(f"Se ha añadido la canción a la cola: {cancion}")
            await ctx.message.add_reaction("✅")

        except yt_handler.YTError as e:
            await ctx.send(f"Error al buscar la canción: {e}")

    @bot.command(name="skip", aliases=["saltar"])
    async def skip_music(ctx):
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
        guild_id = ctx.guild.id
        if guild_id not in queues:
            await ctx.send("No hay canciones en la cola.")
            return
        queue = queues[guild_id]
        queue.clear_queue()
        await ctx.send("Cola de canciones limpiada.")

    @bot.command(name="np", aliases=["nowplaying", "reproduciendo"])
    async def now_playing(ctx):
        guild_id = ctx.guild.id
        if guild_id not in queues:
            await ctx.send("No hay canciones en la cola.")
            return
        queue = queues[guild_id]
        if queue.now_playing is None:
            await ctx.send("No hay canciones reproduciéndose.")
            return
            
        cancion = queue.now_playing  # Use now_playing directly
        print(f"Now playing: {cancion.__dict__}")
        embed = discord.Embed(
            title="Ahora Reproduciendo",
            description=f"**{cancion.nombrecancion}**\n"
                        f"**Artista:** {cancion.uploadercancion}\n"
                        f"**Duración:** {cancion.duration // 60}:{cancion.duration % 60:02d}\n"
                        f"**Solicitado por:** {cancion.requester}",
            color=0x00ff00
        )
        embed.set_thumbnail(url=cancion.thumbnail)
        await ctx.send(embed=embed)