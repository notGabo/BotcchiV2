from __future__ import annotations

import discord
from discord.ext import commands

from botcchi.models import Requester
from botcchi.services.errors import MusicError, VoiceChannelError
from botcchi.services.player import GuildPlayer, PlayerManager
from botcchi.services.resolver import MediaResolver
from botcchi.ui.embeds import (
    error_embed,
    info_embed,
    now_playing_embed,
    queue_embed,
    queued_embed,
    success_embed,
    warning_embed,
)


class MusicCog(commands.Cog, name="Musica"):
    def __init__(self, resolver: MediaResolver, players: PlayerManager) -> None:
        self.resolver = resolver
        self.players = players

    @staticmethod
    def _requester(ctx: commands.Context) -> Requester:
        avatar = getattr(ctx.author.display_avatar, "url", None)
        return Requester(
            display_name=ctx.author.display_name,
            avatar_url=str(avatar) if avatar else None,
        )

    @staticmethod
    def _author_voice_channel(ctx: commands.Context) -> discord.VoiceChannel:
        if not isinstance(ctx.author, discord.Member):
            raise VoiceChannelError("Este comando solo funciona dentro de un servidor.")
        voice_state = ctx.author.voice
        if not voice_state or not isinstance(voice_state.channel, discord.VoiceChannel):
            raise VoiceChannelError("Debes entrar a un canal de voz primero.")
        return voice_state.channel

    async def _connect(self, ctx: commands.Context, player: GuildPlayer) -> None:
        channel = self._author_voice_channel(ctx)
        voice = ctx.voice_client
        if voice is None:
            try:
                await channel.connect(self_deaf=True)
            except (
                discord.ClientException,
                discord.OpusNotLoaded,
                discord.HTTPException,
            ) as exc:
                raise VoiceChannelError(
                    "No pude conectarme al canal de voz. Revisa mis permisos."
                ) from exc
            return

        if voice.channel != channel:
            if player.is_active:
                raise VoiceChannelError(
                    f"Ya estoy reproduciendo musica en {voice.channel.mention}."
                )
            await voice.move_to(channel)

    def _player_for(self, ctx: commands.Context) -> GuildPlayer:
        if ctx.guild is None:
            raise VoiceChannelError("Este comando solo funciona dentro de un servidor.")
        return self.players.get(ctx.guild.id)

    def _require_same_voice(self, ctx: commands.Context) -> GuildPlayer:
        player = self._player_for(ctx)
        channel = self._author_voice_channel(ctx)
        voice = ctx.voice_client
        if voice is None or not voice.is_connected():
            raise VoiceChannelError("No estoy conectado a ningun canal de voz.")
        if voice.channel != channel:
            raise VoiceChannelError(
                f"Debes estar conmigo en {voice.channel.mention} para usar ese comando."
            )
        return player

    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx: commands.Context, *, query: str) -> None:
        """Resolve and enqueue one YouTube or Spotify track."""
        try:
            player = self._player_for(ctx)
            self._author_voice_channel(ctx)
            async with ctx.typing():
                track = await self.resolver.resolve_track(
                    query.strip(), self._requester(ctx)
                )
                await self._connect(ctx, player)
                started, position = await player.enqueue(track, ctx.channel)
            if not started:
                await ctx.send(embed=queued_embed(track, position))
        except MusicError as exc:
            await ctx.send(embed=error_embed("No se pudo reproducir", str(exc)))

    @commands.command(name="playlist", aliases=["pl"])
    async def playlist(self, ctx: commands.Context, url: str) -> None:
        """Resolve and enqueue a YouTube or Spotify playlist."""
        try:
            player = self._player_for(ctx)
            self._author_voice_channel(ctx)
            async with ctx.typing():
                tracks = await self.resolver.resolve_playlist(
                    url.strip(), self._requester(ctx)
                )
                await self._connect(ctx, player)
                await player.enqueue_many(tracks, ctx.channel)
            await ctx.send(
                embed=success_embed(
                    "Playlist anadida",
                    f"Se agregaron **{len(tracks)} canciones** a la cola.",
                )
            )
        except MusicError as exc:
            await ctx.send(embed=error_embed("No se pudo cargar la playlist", str(exc)))

    @commands.command(name="skip", aliases=["s"])
    async def skip(self, ctx: commands.Context) -> None:
        try:
            player = self._require_same_voice(ctx)
            if not player.skip():
                await ctx.send(
                    embed=warning_embed(
                        "Nada que saltar", "No hay una cancion reproduciendose."
                    )
                )
                return
            await ctx.send(
                embed=success_embed("Cancion saltada", "Pasando a la siguiente cancion.")
            )
        except MusicError as exc:
            await ctx.send(embed=error_embed("No se pudo saltar", str(exc)))

    @commands.command(name="stop", aliases=["leave", "disconnect"])
    async def stop(self, ctx: commands.Context) -> None:
        try:
            player = self._require_same_voice(ctx)
            await player.stop_and_disconnect()
            await ctx.send(
                embed=success_embed(
                    "Reproduccion detenida", "Limpie la cola y sali del canal de voz."
                )
            )
        except MusicError as exc:
            await ctx.send(embed=error_embed("No se pudo detener", str(exc)))

    @commands.command(name="clear")
    async def clear(self, ctx: commands.Context) -> None:
        try:
            player = self._require_same_voice(ctx)
            removed = player.clear()
            await ctx.send(
                embed=success_embed(
                    "Cola limpiada", f"Se eliminaron **{removed} canciones** pendientes."
                )
            )
        except MusicError as exc:
            await ctx.send(embed=error_embed("No se pudo limpiar", str(exc)))

    @commands.command(name="queue", aliases=["q", "cola"])
    async def queue(self, ctx: commands.Context) -> None:
        try:
            player = self._player_for(ctx)
            current, tracks = player.snapshot()
            await ctx.send(embed=queue_embed(current, tracks))
        except MusicError as exc:
            await ctx.send(embed=error_embed("No se pudo mostrar la cola", str(exc)))

    @commands.command(name="np", aliases=["nowplaying"])
    async def now_playing(self, ctx: commands.Context) -> None:
        try:
            player = self._player_for(ctx)
            if player.current is None:
                await ctx.send(
                    embed=info_embed(
                        "Sin reproduccion", "No hay ninguna cancion reproduciendose."
                    )
                )
                return
            await ctx.send(embed=now_playing_embed(player.current))
        except MusicError as exc:
            await ctx.send(embed=error_embed("No se pudo consultar", str(exc)))

    @commands.command(name="lyrics", aliases=["letra"])
    async def lyrics(self, ctx: commands.Context) -> None:
        await ctx.send(
            embed=warning_embed(
                "Lyrics [WIP]",
                "La busqueda de letras esta en desarrollo y estara disponible pronto.",
            )
        )
