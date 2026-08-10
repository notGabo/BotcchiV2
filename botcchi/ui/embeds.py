from __future__ import annotations

from collections.abc import Sequence

import discord

from botcchi.models import Track
from botcchi.utils.formatting import format_duration, truncate

SUCCESS = discord.Color.from_rgb(0, 255, 35)
INFO = discord.Color.from_rgb(88, 101, 242)
WARNING = discord.Color.from_rgb(250, 166, 26)
ERROR = discord.Color.from_rgb(237, 66, 69)
NEUTRAL = discord.Color.from_rgb(46, 204, 113)


def base_embed(title: str, description: str | None = None, *, color=INFO) -> discord.Embed:
    return discord.Embed(title=title, description=description, color=color)


def success_embed(title: str, description: str) -> discord.Embed:
    return base_embed(title, description, color=SUCCESS)


def info_embed(title: str, description: str) -> discord.Embed:
    return base_embed(title, description, color=INFO)


def warning_embed(title: str, description: str) -> discord.Embed:
    return base_embed(title, description, color=WARNING)


def error_embed(title: str, description: str) -> discord.Embed:
    return base_embed(title, description, color=ERROR)


def track_embed(
    track: Track,
    *,
    heading: str,
    footer: str | None = None,
    color=SUCCESS,
) -> discord.Embed:
    embed = discord.Embed(
        title=heading,
        description=f"[{discord.utils.escape_markdown(track.display_title)}]({track.webpage_url})",
        color=color,
    )
    if track.thumbnail:
        embed.set_thumbnail(url=track.thumbnail)
    embed.add_field(name="Duración", value=format_duration(track.duration), inline=True)
    embed.add_field(
        name="Subido por", value=truncate(track.uploader, 100), inline=True
    )
    embed.add_field(
        name="Pedido por", value=truncate(track.requester.display_name, 100), inline=True
    )
    if footer:
        embed.set_footer(text=truncate(footer, 2048))
    return embed


def now_playing_embed(track: Track) -> discord.Embed:
    footer = (
        f"Se ha añadido la canción a la cola: {track.display_title} - {track.uploader} "
        f"({format_duration(track.duration)})"
    )
    return track_embed(track, heading="Reproduciendo", footer=footer)


def queued_embed(track: Track, position: int) -> discord.Embed:
    footer = (
        f"Se ha añadido la canción a la cola: {track.display_title} - "
        f"{track.uploader} ({format_duration(track.duration)})"
    )
    embed = track_embed(track, heading="Añadida a la cola", footer=footer, color=NEUTRAL)
    embed.add_field(name="Posición", value=str(position), inline=True)
    return embed


def queue_embed(current: Track | None, tracks: Sequence[Track]) -> discord.Embed:
    embed = base_embed("Cola de reproduccion", color=NEUTRAL)
    if current:
        embed.add_field(
            name="Reproduciendo ahora",
            value=f"[{truncate(current.display_title, 80)}]({current.webpage_url})",
            inline=False,
        )
    if not tracks:
        embed.description = "No hay canciones esperando en la cola."
        return embed

    lines = [
        f"`{index}.` [{truncate(track.display_title, 65)}]({track.webpage_url}) "
        f"`{format_duration(track.duration)}`"
        for index, track in enumerate(tracks[:20], start=1)
    ]
    if len(tracks) > 20:
        lines.append(f"\n... y {len(tracks) - 20} canciones más.")
    embed.description = "\n".join(lines)
    embed.set_footer(text=f"{len(tracks)} canción(es) en espera")
    return embed


def commands_embed(prefix: str) -> discord.Embed:
    embed = base_embed(
        "Comandos de Botcchi",
        "Controles disponibles para la reproducción de música.",
        color=NEUTRAL,
    )
    commands = (
        ("comandos", "Muestra este mensaje."),
        ("ping", "Responde con 'Pong!'."),
        ("play [canción o URL]", "Reproduce una canción."),
        ("playlist [URL]", "Carga una playlist de Spotify o YouTube."),
        ("skip", "Pasa a la siguiente canción."),
        ("stop", "Detiene la música y desconecta al bot."),
        ("clear", "Limpia las canciones pendientes."),
        ("queue", "Muestra las canciones en cola."),
        ("np", "Muestra la canción en reproducción."),
        ("lyrics", "[WIP] Letra de la canción actual."),
    )
    for command, description in commands:
        embed.add_field(
            name=f"{prefix}{command}", value=description, inline=False
        )
    return embed
