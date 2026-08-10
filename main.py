from __future__ import annotations

import asyncio
import logging
from contextlib import suppress

from botcchi.bot import Botcchi
from botcchi.config import Settings, SettingsError
from botcchi.logging_config import configure_logging


async def main() -> None:
    configure_logging()
    logger = logging.getLogger(__name__)

    try:
        settings = Settings.from_env()
    except SettingsError as exc:
        logger.critical("Configuracion invalida: %s", exc)
        raise SystemExit(1) from exc

    bot = Botcchi(settings)
    async with bot:
        await bot.start(settings.bot_token)


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        asyncio.run(main())
