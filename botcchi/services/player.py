from __future__ import annotations

import asyncio
import logging
from collections import deque
from collections.abc import Sequence

import discord
from discord.ext import commands

from botcchi.models import Track
from botcchi.services.errors import MediaExtractionError
from botcchi.services.youtube import YouTubeService
from botcchi.ui.embeds import error_embed, now_playing_embed

logger = logging.getLogger(__name__)

FFMPEG_BEFORE_OPTIONS = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
FFMPEG_OPTIONS = "-vn -loglevel warning"


class GuildPlayer:
    def __init__(
        self,
        bot: commands.Bot,
        guild_id: int,
        youtube: YouTubeService,
    ) -> None:
        self.bot = bot
        self.guild_id = guild_id
        self.youtube = youtube
        self.queue: deque[Track] = deque()
        self.current: Track | None = None
        self.text_channel: discord.abc.Messageable | None = None
        self._transition_lock = asyncio.Lock()
        self._starting = False
        self._stopping = False

    @property
    def voice_client(self) -> discord.VoiceClient | None:
        guild = self.bot.get_guild(self.guild_id)
        return guild.voice_client if guild else None

    @property
    def is_active(self) -> bool:
        voice = self.voice_client
        return bool(self.current or self._starting or (voice and voice.is_playing()))

    async def enqueue(
        self, track: Track, channel: discord.abc.Messageable
    ) -> tuple[bool, int]:
        accepted_as_current = not self.is_active and not self.queue
        self.queue.append(track)
        self.text_channel = channel
        position = len(self.queue)
        await self.start_if_idle()
        return accepted_as_current, position

    async def enqueue_many(
        self, tracks: Sequence[Track], channel: discord.abc.Messageable
    ) -> bool:
        self.queue.extend(tracks)
        self.text_channel = channel
        return await self.start_if_idle()

    async def start_if_idle(self) -> bool:
        async with self._transition_lock:
            voice = self.voice_client
            if (
                self._stopping
                or self._starting
                or self.current is not None
                or voice is None
                or not voice.is_connected()
                or voice.is_playing()
                or voice.is_paused()
                or not self.queue
            ):
                return False
            self._starting = True
            track = self.queue.popleft()
            self.current = track

        try:
            stream_url = await self.youtube.stream_url(track)
            source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(
                    stream_url,
                    before_options=FFMPEG_BEFORE_OPTIONS,
                    options=FFMPEG_OPTIONS,
                ),
                volume=0.5,
            )
        except (MediaExtractionError, discord.ClientException, OSError) as exc:
            logger.exception("No se pudo iniciar la pista %s", track.display_title)
            async with self._transition_lock:
                self.current = None
                self._starting = False
            await self._send(
                error_embed("Error de reproduccion", str(exc))
            )
            await self.start_if_idle()
            return False

        loop = asyncio.get_running_loop()

        def after_playback(error: Exception | None) -> None:
            loop.call_soon_threadsafe(
                asyncio.create_task, self._on_track_end(error)
            )

        playback_error: Exception | None = None
        async with self._transition_lock:
            voice = self.voice_client
            if voice is None or not voice.is_connected() or self._stopping:
                source.cleanup()
                self.current = None
                self._starting = False
                return False
            try:
                voice.play(source, after=after_playback)
            except (discord.ClientException, TypeError) as exc:
                source.cleanup()
                self.current = None
                self._starting = False
                playback_error = exc
            else:
                self._starting = False

        if playback_error:
            await self._send(error_embed("Error de reproduccion", str(playback_error)))
            await self.start_if_idle()
            return False

        await self._send(now_playing_embed(track))
        return True

    async def _on_track_end(self, error: Exception | None) -> None:
        if error:
            logger.error("FFmpeg finalizo con error en %s: %s", self.guild_id, error)
            await self._send(
                error_embed(
                    "Error de FFmpeg",
                    "La cancion termino de forma inesperada. Intentare continuar la cola.",
                )
            )

        async with self._transition_lock:
            self.current = None
            if self._stopping:
                return
        await self.start_if_idle()

    def skip(self) -> bool:
        voice = self.voice_client
        if voice and (voice.is_playing() or voice.is_paused()):
            voice.stop()
            return True
        return False

    def clear(self) -> int:
        count = len(self.queue)
        self.queue.clear()
        return count

    async def stop_and_disconnect(self) -> None:
        async with self._transition_lock:
            self._stopping = True
            self.queue.clear()
            voice = self.voice_client
            if voice and (voice.is_playing() or voice.is_paused()):
                voice.stop()

        if voice and voice.is_connected():
            await voice.disconnect(force=True)

        async with self._transition_lock:
            self.current = None
            self._starting = False
            self._stopping = False

    def snapshot(self) -> tuple[Track | None, list[Track]]:
        return self.current, list(self.queue)

    async def _send(self, embed: discord.Embed) -> None:
        if not self.text_channel:
            return
        try:
            await self.text_channel.send(embed=embed)
        except discord.HTTPException:
            logger.exception("No se pudo enviar un embed en el servidor %s", self.guild_id)


class PlayerManager:
    def __init__(self, bot: commands.Bot, youtube: YouTubeService) -> None:
        self.bot = bot
        self.youtube = youtube
        self._players: dict[int, GuildPlayer] = {}

    def get(self, guild_id: int) -> GuildPlayer:
        if guild_id not in self._players:
            self._players[guild_id] = GuildPlayer(self.bot, guild_id, self.youtube)
        return self._players[guild_id]

    async def close(self) -> None:
        await asyncio.gather(
            *(player.stop_and_disconnect() for player in self._players.values()),
            return_exceptions=True,
        )
        self._players.clear()
