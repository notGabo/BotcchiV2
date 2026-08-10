import asyncio

from botcchi.bot import Botcchi
from botcchi.config import Settings


def test_bot_registers_all_requested_commands() -> None:
    settings = Settings(
        bot_token="test-token",
        bot_prefix="--",
        app_id=None,
        public_key=None,
        bot_url_invitacion=None,
        allowed_guild_ids=frozenset(),
        spotify_client_id=None,
        spotify_client_secret=None,
        cookies_browser=None,
        cookies_file=None,
    )

    async def load_commands() -> set[str]:
        bot = Botcchi(settings)
        await bot.setup_hook()
        names = {command.name for command in bot.commands}
        await bot.close()
        return names

    command_names = asyncio.run(load_commands())

    assert {
        "comandos",
        "ping",
        "play",
        "playlist",
        "skip",
        "stop",
        "clear",
        "queue",
        "np",
        "lyrics",
    } <= command_names
