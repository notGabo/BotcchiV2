import asyncio
import logging
import traceback
import discord
from discord.ext import commands
from src.config import BOT_TOKEN, BOT_PREFIX, BOT_SERVIDORES_PERMITIDOS

# Configuración global de Logging en consola
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("Bot")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents, help_command=None)


@bot.event
async def on_ready():
    logger.info(f"Bot conectado como {bot.user.name}")


@bot.event
async def on_command_error(ctx, error):
    """Captura cualquier excepción no controlada en los comandos y muestra el log."""
    logger.error(f"Error al ejecutar el comando '{ctx.command}': {error}")
    traceback.print_exception(type(error), error, error.__traceback__)


@bot.check
async def check_guilds(ctx):
    if BOT_SERVIDORES_PERMITIDOS and ctx.guild:
        return ctx.guild.id in BOT_SERVIDORES_PERMITIDOS
    return True


async def main():
    async with bot:
        await bot.load_extension("src.cogs.general")
        await bot.load_extension("src.cogs.music")
        await bot.start(BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())