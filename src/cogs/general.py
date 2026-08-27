import discord
from discord.ext import commands
from src.utils.embed_builder import EmbedBuilder


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx):
        await ctx.send(embed=EmbedBuilder.info("Pong!", f"Latencia: {round(self.bot.latency * 1000)}ms"))

    @commands.command(name="help", aliases=["comandos"])
    async def help_command(self, ctx):
        embed = discord.Embed(
            title="Lista de Comandos",
            color=discord.Color.blue()
        )
        cmds = {
            "🔹comandos": "Muestra la lista de comandos disponibles.",
            "🔹ping": "Responde con 'Pong!' y la latencia actual del bot.",
            "🔹play [canción o url]": "Reproduce una canción de YouTube o busca por palabras clave.",
            "🔹playlist [url]": "Carga y añade a la cola una lista de reproducción de YouTube o Spotify.",
            "🔹skip": "Salta a la siguiente canción en la cola.",
            "🔹stop": "Detiene la música, limpia la cola y desconecta al bot del canal de voz.",
            "🔹clear": "Limpia la cola de reproducción en caso de problemas.",
            "🔹queue": "Muestra las canciones en la cola de reproducción.",
            "🔹np": "Muestra la canción que se está reproduciendo actualmente.",
            "🔹lyrics": "[WIP] Muestra la letra de la canción en reproducción."
        }
        for cmd, desc in cmds.items():
            embed.add_field(name=cmd, value=desc, inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(General(bot))
