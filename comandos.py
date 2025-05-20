from discord.ext import commands
from discord import embeds
import yt_handler
import constantes
import utils

# Comandos bot
async def setup(bot):
    @bot.command(name="comandos", aliases=["ayuda","","help"])
    async def list_commands(ctx):
        embed = embeds.Embed(
            title="Comandos disponibles",
            description="Aquí tienes una lista de los comandos disponibles:",
            color=0x00ff00
        )

        embed.add_field(name=f"🔹comandos", value="Muestra este mensaje", inline=False)
        embed.add_field(name=f"🔹ping", value="Responde con 'Pong!'", inline=False)
        embed.add_field(name=f"🔹play [canción o url]", value="Reproduce una canción", inline=False)
        embed.add_field(name=f"🔹stop", value="Desconecta al bot", inline=False)

        embed.set_footer(text=f"Usa el prefijo {constantes.BOT_PREFIX} para los comandos de texto.")

        await ctx.send(embed=embed)

    @bot.command(name="ping")
    async def ping_command(ctx):
        await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

    @bot.command(name="play",aliases=["reproducir"])
    async def play_music(ctx, arg):
        # TODO: Funcion para limpiar los argumentos o separar un string en varios argumentos. Ej: usuario diferencia entre canción y playlist. de ser playlist en función de yt_dlp marcar ydl_options como True.
        if ctx.author.voice is None:
            await ctx.send("Necesitas estar en un canal de voz para usar este comando")
            return
        voice_channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await voice_channel.connect()
        else:
            await ctx.voice_client.move_to(voice_channel)
        await ctx.message.add_reaction("✅")


    @bot.command(name="stop",aliases=["pausar","detener","disconnect"])
    async def stop_music(ctx):
        if ctx.voice_client is None:
            await ctx.send("No estoy conectado a ningún canal de voz.")
        try:
            await ctx.voice_client.disconnect()
            await ctx.message.add_reaction("👋")
        except Exception as e:
            await ctx.send(f"Error al desconectar: {e}")
        return