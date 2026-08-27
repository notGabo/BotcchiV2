import asyncio
import discord
from discord.ext import commands
from src.config import BOT_TOKEN, BOT_PREFIX, BOT_SERVIDORES_PERMITIDOS

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents, help_command=None)
bot.remove_command("help")


@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user.name}")


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
