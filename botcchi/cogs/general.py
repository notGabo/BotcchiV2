from __future__ import annotations

from discord.ext import commands

from botcchi.config import Settings
from botcchi.ui.embeds import commands_embed, info_embed


class GeneralCog(commands.Cog, name="General"):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @commands.command(name="comandos", aliases=["help", "ayuda"])
    async def show_commands(self, ctx: commands.Context) -> None:
        """Show all available prefix commands."""
        await ctx.send(embed=commands_embed(self.settings.bot_prefix))

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context) -> None:
        latency_ms = round(ctx.bot.latency * 1000)
        await ctx.send(
            embed=info_embed("Pong!", f"Latencia: `{latency_ms} ms`")
        )
