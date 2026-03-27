from discord.ext import commands
from discord import app_commands
import discord
import src.constantes as constantes


# Setup function para registrar los slash commands
async def setup(bot: commands.Bot):
    """
    Registra todos los slash commands del bot.
    Esta función debe ser llamada desde el setup_hook en main.py
    """
    
    @bot.tree.command(name='ping', description='Hace un ping desde el bot al servidor de discord')
    @app_commands.describe()
    async def ping(interaction: discord.Interaction):
        """
        Comando slash para verificar la latencia del bot.
        Responde con el tiempo de respuesta en milisegundos.
        """
        latencia = round(bot.latency * 1000)
        
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Latencia: **{latencia}ms**",
            color=0x00ff00 if latencia < 200 else 0xffa500 if latencia < 500 else 0xff0000
        )
        
        # Añadir información adicional de healthcheck
        embed.add_field(
            name="Estado",
            value="✅ Operacional" if latencia < 500 else "⚠️ Latencia alta",
            inline=True
        )
        embed.add_field(
            name="Servidores",
            value=f"{len(bot.guilds)}",
            inline=True
        )
        embed.add_field(
            name="Canales de voz",
            value=f"{len(bot.voice_clients)}",
            inline=True
        )
        
        embed.set_footer(text=f"{constantes.BOT_NAME}")
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name='estado', description='Revisa el estado del bot. Sus conexiones y si está activo')
    @app_commands.describe()
    async def estado(interaction: discord.Interaction):
        """
        Comando slash para verificar el estado general del bot.
        Muestra información sobre conexiones, latencia y servidores.
        """
        latencia = round(bot.latency * 1000)
        
        embed = discord.Embed(
            title=f"📊 Estado de {constantes.BOT_NAME}",
            description="Información del estado actual del bot",
            color=0x00ff00
        )
        
        embed.add_field(
            name="🏓 Latencia",
            value=f"{latencia}ms",
            inline=True
        )
        embed.add_field(
            name="🖥️ Servidores",
            value=f"{len(bot.guilds)} {'servidor' if len(bot.guilds) == 1 else 'servidores'}",
            inline=True
        )
        embed.add_field(
            name="🔊 Canales de voz",
            value=f"{len(bot.voice_clients)} {'conectado' if len(bot.voice_clients) == 1 else 'conectados'}",
            inline=True
        )
        
        # Estado general
        estado_general = "✅ Operacional" if latencia < 500 else "⚠️ Latencia alta"
        embed.add_field(
            name="Estado General",
            value=estado_general,
            inline=False
        )
        
        embed.set_footer(text=f"{constantes.BOT_NAME}")
        
        await interaction.response.send_message(embed=embed)
