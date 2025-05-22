import asyncio
import discord

class Cancion:
    def __init__(
            self,
            nombrecancion: str,
            uploadercancion: str,
            thumbnail: str,
            urlcancion: str,
            urlytdlp: str,
            duration: int,
            requester: str,
            loop: bool = False,
    ):
        self.nombrecancion = nombrecancion
        self.uploadercancion = uploadercancion
        self.thumbnail = thumbnail
        self.urlffmpeg = urlytdlp
        self.urlcancion = urlcancion
        self.duration = duration
        self.requester = requester
        self.loop = loop

    def __str__(self):
        return f"{self.nombrecancion} - {self.uploadercancion} ({self.duration // 60}:{self.duration % 60:02d})"

class QueueHandler:
    def __init__(
            self,
            queue = [],
            current_song = None,
            now_playing = None,
            loop_queue = False,
            is_playing = False,
            voice_channel = None,
            ctx = None
        ):
        self.queue = queue
        self.current_song = current_song
        self.now_playing = now_playing
        self.loop_queue = loop_queue
        self.is_playing = is_playing
        self.voice_channel = voice_channel
        self.ctx = ctx

    async def play_cancion(self, cancion: Cancion):
        ffmpeg_opts = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn",
        }
        if self.voice_channel is None:
            await self.ctx.message.add_reaction("❌")
            await self.ctx.send("Necesitas estar en un canal de voz para usar este comando")
            return

        if self.ctx.voice_client is None:
            await self.voice_channel.connect()

        fuente = discord.FFmpegPCMAudio(cancion.urlffmpeg, **ffmpeg_opts)
        voice_client = self.ctx.voice_client or await self.voice_channel.connect()
        voice_client.play(fuente, after=lambda e: print(f"Error al reproducir: {e}") if e else None)

        await self.ctx.message.add_reaction("✅")
        await self.ctx.send(f"Reproduciendo: {cancion}")

    async def play_next(self):
        if self.queue:
            self.is_playing = True
            self.now_playing = self.current_song
            self.current_song = self.queue.pop(0)
            await self.play_cancion(self.current_song)
        else:
            self.is_playing = False
            self.current_song = None
            self.now_playing = None

    def add_cancion(self, cancion: Cancion):
        self.queue.append(cancion)
        for i in self.queue:
            print(f"Cola: {i.nombrecancion} - {i.uploadercancion} ({i.duration // 60}:{i.duration % 60:02d})")
        if not self.is_playing:
            asyncio.create_task(self.play_next())
    async def skip_cancion(self):
        await self.play_next()

    def stop(self):
        self.queue.clear()
        self.current_song = None
        self.now_playing = None
        self.is_playing = False
        if self.voice_client:
            asyncio.create_task(self.voice_client.disconnect())
            self.voice_client = None

    def clear_queue(self):
        self.queue.clear()
        self.current_song = None
        self.now_playing = None
        self.is_playing = False

    # async def now_playing_info(self):
    #     if self.current_song:
    #         await self.ctx.send(f"Reproduciendo: {self.current_song}")
    #     else:
    #         await self.ctx.send("No hay canciones en la cola.")