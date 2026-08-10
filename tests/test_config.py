import pytest

from botcchi.config import Settings, SettingsError

ENV_KEYS = (
    "BOT_TOKEN",
    "BOT_PREFIX",
    "APP_ID",
    "PUBLIC_KEY",
    "BOT_URL_INVITACION",
    "BOT_SERVIDORES_PERMITIDOS",
    "SPOTIFY_CLIENT_ID",
    "SPOTIFY_CLIENT_SECRET",
    "COOKIES_BROWSER",
    "COOKIES_FILE",
)


def clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_settings_load_required_and_guilds(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    clear_env(monkeypatch)
    monkeypatch.setenv("BOT_TOKEN", "secret")
    monkeypatch.setenv("BOT_PREFIX", "--")
    monkeypatch.setenv("APP_ID", "123")
    monkeypatch.setenv("BOT_SERVIDORES_PERMITIDOS", "10, 20;30")

    settings = Settings.from_env(tmp_path / "missing.env")

    assert settings.bot_token == "secret"
    assert settings.bot_prefix == "--"
    assert settings.app_id == 123
    assert settings.allowed_guild_ids == frozenset({10, 20, 30})
    assert settings.guild_is_allowed(20)
    assert not settings.guild_is_allowed(99)


def test_settings_require_token_and_prefix(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    clear_env(monkeypatch)
    with pytest.raises(SettingsError, match="BOT_TOKEN"):
        Settings.from_env(tmp_path / "missing.env")


def test_spotify_credentials_are_a_pair(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    clear_env(monkeypatch)
    monkeypatch.setenv("BOT_TOKEN", "secret")
    monkeypatch.setenv("BOT_PREFIX", "!")
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "client")

    with pytest.raises(SettingsError, match="deben configurarse juntos"):
        Settings.from_env(tmp_path / "missing.env")
