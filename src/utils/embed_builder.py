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
    @staticmethod
    def queue(current: dict | None, queue_list: list) -> discord.Embed:
        embed = discord.Embed(
            title="Lista de canciones en la cola",
            color=discord.Color.green()
        )

        # Configurar portada de la canción actual
        if current and current.get('info', {}).get('thumbnail'):
            embed.set_thumbnail(url=current['info']['thumbnail'])

        current_title = current['info']['title'] if current else "None"
        description_lines = [f"Reproduciendo ahora: **{current_title}**\n"]

        if not queue_list:
            description_lines.append("*No hay más canciones en la cola.*")
        else:
            # Mostrar hasta 10 canciones para no saturar los límites de caracteres de Discord
            for item in queue_list[:10]:
                info = item.get('info', {})
                requester = item.get('requester', 'Desconocido')
                title = info.get('title', 'Sin título')
                uploader = info.get('uploader', 'Desconocido')
                duration = info.get('duration_str', '0:00')

                description_lines.append(
                    f"**{title}**\n"
                    f"Artista: {uploader} | Duración: {duration} | Solicitado por: {requester}\n"
                )

            if len(queue_list) > 10:
                description_lines.append(f"*...y {len(queue_list) - 10} canciones más en espera.*")

        embed.description = "\n".join(description_lines)
        return embed