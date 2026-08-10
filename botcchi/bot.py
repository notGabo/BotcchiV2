from __future__ import annotations

import logging

import discord
from discord.ext import commands

from botcchi.cogs.general import GeneralCog
from botcchi.cogs.music import MusicCog
from botcchi.config import Settings
from botcchi.services.player import PlayerManager
from botcchi.services.resolver import MediaResolver
from botcchi.services.spotify import SpotifyService
from botcchi.services.youtube import YouTubeService
from botcchi.ui.embeds import error_embed

logger = logging.getLogger(__name__)


class Botcchi(commands.Bot):
    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True

        super().__init__(
            command_prefix=settings.bot_prefix,
            intents=intents,
            help_command=None,
            application_id=settings.app_id,
            allowed_mentions=discord.AllowedMentions(
                everyone=False, roles=False, replied_user=False
            ),
            case_insensitive=True,
        )
        self.settings = settings
        self.youtube = YouTubeService(settings)
        self.spotify = SpotifyService(settings)
        self.resolver = MediaResolver(self.youtube, self.spotify)
        self.players = PlayerManager(self, self.youtube)
        self.add_check(self._allowed_guild)

    async def setup_hook(self) -> None:
        await self.add_cog(GeneralCog(self.settings))
        await self.add_cog(MusicCog(self.resolver, self.players))

    async def close(self) -> None:
        await self.players.close()
        await super().close()

    async def on_ready(self) -> None:
        if self.user:
            logger.info(
                "Conectado como %s (%s) en %s servidor(es)",
                self.user,
                self.user.id,
                len(self.guilds),
            )

    async def _allowed_guild(self, ctx: commands.Context) -> bool:
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        if not self.settings.guild_is_allowed(ctx.guild.id):
            raise commands.CheckFailure("Servidor no permitido")
        return True

    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        if hasattr(ctx.command, "on_error"):
            return

        error = getattr(error, "original", error)
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(
                embed=error_embed(
                    "Comando desconocido",
                    f"Usa `{self.settings.bot_prefix}comandos` para ver la lista disponible.",
                )
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            usage = f"{self.settings.bot_prefix}{ctx.command.qualified_name}"
            signature = ctx.command.signature
            await ctx.send(
                embed=error_embed(
                    "Falta un argumento", f"Uso correcto: `{usage} {signature}`"
                )
            )
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(
                embed=error_embed(
                    "Servidor requerido", "Los comandos no estan disponibles por mensaje directo."
                )
            )
        elif isinstance(error, commands.CheckFailure):
            await ctx.send(
                embed=error_embed(
                    "Servidor no permitido",
                    "Este bot no esta habilitado para responder en este servidor.",
                )
            )
        elif isinstance(error, commands.BotMissingPermissions):
            missing = ", ".join(error.missing_permissions)
            await ctx.send(
                embed=error_embed("Permisos insuficientes", f"Me faltan: `{missing}`")
            )
        else:
            logger.exception(
                "Error no controlado en el comando %s", ctx.command, exc_info=error
            )
            await ctx.send(
                embed=error_embed(
                    "Error inesperado",
                    "Ocurrio un error interno al ejecutar el comando.",
                )
            )
