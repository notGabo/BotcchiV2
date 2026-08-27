import discord


class EmbedBuilder:
    @staticmethod
    def now_playing(info: dict, requester_name: str) -> discord.Embed:
        embed = discord.Embed(
            title="Reproduciendo",
            description=f"[{info['title']}]({info['webpage_url']})",
            color=discord.Color.random()
        )
        if info.get('thumbnail'):
            embed.set_thumbnail(url=info['thumbnail'])
        embed.add_field(name="Duración", value=info.get('duration_str', 'Desconocida'), inline=True)
        embed.add_field(name="Subido por", value=info.get('uploader', 'Desconocido'), inline=True)
        embed.add_field(name="Pedido por", value=requester_name, inline=True)
        return embed

    @staticmethod
    def info(title: str, description: str) -> discord.Embed:
        return discord.Embed(title=title, description=description, color=discord.Color.blue())

    @staticmethod
    def error(description: str) -> discord.Embed:
        return discord.Embed(title="Error", description=description, color=discord.Color.red())
