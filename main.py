import discord
from os import execl
from sys import executable, argv
from discord.ext import commands
from discord import app_commands
import src.comandos as comandos
import src.constantes as constantes

intents = discord.Intents.default()
intents.message_content = True
intents.typing = True
intents.presences = True

bot = commands.Bot(
    command_prefix=constantes.BOT_PREFIX,
    intents=intents,
    application_id=constantes.BOT_APP_ID,
    help_command=None
    )

@bot.event
async def setup_hook():
    await comandos.setup(bot) # Logica del bot aqui

@bot.event
async def on_ready():
    print(f'{constantes.BOT_NAME} conectado como {bot.user.name}')
    print(f'ID: {bot.user.id}')
    print('-'*20)
    print('Conectado a los siguientes servidores:')
    for guild in bot.guilds:
        print(f'(GuildID: {guild.id}) {guild.name}')
    print('-'*20)
    # Sincroniza los comandos de barra
    try:
        synced = await bot.tree.sync()
        print(f'Slash commands sincronizados: {len(synced)}')
    except Exception as e:
        print(f'Error al sincronizar slash commands: {e}')

@bot.tree.command(name='ping', description='Hace un ping desde el bot al servidor de discord')
@app_commands.describe()
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f'Pong! {round(bot.latency * 1000)}ms')

@bot.tree.command(name='estado', description='Revisa el estado del bot. Sus conexiones y si está activo')
@app_commands.describe()
async def estado(interaction: discord.Interaction):
    await interaction.response.send_message(f"""
Ping: {round(bot.latency * 1000)}ms
Conectado a {len(bot.guilds)} {'servidor' if len(bot.guilds) == 1  else 'servidores'}
Canales de voz conectados: {len(bot.voice_clients)}
""")

@bot.tree.command(name='restartbot', description='Reinicia el bot en caso de que haya un error')
@app_commands.describe()
async def restartbot(interaction: discord.Interaction):
    print('Reiniciando bot...')
    await interaction.response.send_message(f'Bot reiniciado. Reiniciando...')
    await bot.close()
    # Aparentemente esto no es seguro. Cambiar a un proceso externo mas adelante al momento de deployear en un servidor linux
    execl(executable, executable, *argv)


bot.run(constantes.BOT_TOKEN)