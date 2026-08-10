from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


class SettingsError(ValueError):
    """Raised when the environment configuration is invalid."""


def _optional_path(value: str | None) -> Path | None:
    if not value or not value.strip():
        return None
    return Path(value.strip()).expanduser()


def _parse_guild_ids(value: str | None) -> frozenset[int]:
    if not value or not value.strip():
        return frozenset()

    guild_ids: set[int] = set()
    for raw_id in value.replace(";", ",").split(","):
        raw_id = raw_id.strip()
        if not raw_id:
            continue
        try:
            guild_ids.add(int(raw_id))
        except ValueError as exc:
            raise SettingsError(
                "BOT_SERVIDORES_PERMITIDOS debe contener IDs separados por comas."
            ) from exc
    return frozenset(guild_ids)


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    bot_prefix: str
    app_id: int | None
    public_key: str | None
    bot_url_invitacion: str | None
    allowed_guild_ids: frozenset[int]
    spotify_client_id: str | None
    spotify_client_secret: str | None
    cookies_browser: str | None
    cookies_file: Path | None

    @classmethod
    def from_env(cls, env_file: str | Path = ".env") -> Settings:
        load_dotenv(dotenv_path=env_file, override=False)

        token = os.getenv("BOT_TOKEN", "").strip()
        prefix = os.getenv("BOT_PREFIX", "").strip()
        if not token:
            raise SettingsError("BOT_TOKEN es obligatorio.")
        if not prefix:
            raise SettingsError("BOT_PREFIX es obligatorio.")

        raw_app_id = os.getenv("APP_ID", "").strip()
        try:
            app_id = int(raw_app_id) if raw_app_id else None
        except ValueError as exc:
            raise SettingsError("APP_ID debe ser un numero entero.") from exc

        spotify_id = os.getenv("SPOTIFY_CLIENT_ID", "").strip() or None
        spotify_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip() or None
        if bool(spotify_id) != bool(spotify_secret):
            raise SettingsError(
                "SPOTIFY_CLIENT_ID y SPOTIFY_CLIENT_SECRET deben configurarse juntos."
            )

        return cls(
            bot_token=token,
            bot_prefix=prefix,
            app_id=app_id,
            public_key=os.getenv("PUBLIC_KEY", "").strip() or None,
            bot_url_invitacion=os.getenv("BOT_URL_INVITACION", "").strip() or None,
            allowed_guild_ids=_parse_guild_ids(
                os.getenv("BOT_SERVIDORES_PERMITIDOS")
            ),
            spotify_client_id=spotify_id,
            spotify_client_secret=spotify_secret,
            cookies_browser=os.getenv("COOKIES_BROWSER", "").strip() or None,
            cookies_file=_optional_path(os.getenv("COOKIES_FILE")),
        )

    @property
    def spotify_enabled(self) -> bool:
        return bool(self.spotify_client_id and self.spotify_client_secret)

    def guild_is_allowed(self, guild_id: int) -> bool:
        return not self.allowed_guild_ids or guild_id in self.allowed_guild_ids
