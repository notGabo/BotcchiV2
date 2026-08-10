import asyncio
from types import SimpleNamespace

from botcchi.services.player import GuildPlayer


class FakeVoiceClient:
    def __init__(self) -> None:
        self.connected = True
        self.disconnected = False

    def is_connected(self) -> bool:
        return self.connected

    def is_playing(self) -> bool:
        return False

    def is_paused(self) -> bool:
        return False

    async def disconnect(self, *, force: bool) -> None:
        assert force is True
        self.connected = False
        self.disconnected = True


class FakeChannel:
    def __init__(self) -> None:
        self.embeds = []

    async def send(self, *, embed) -> None:
        self.embeds.append(embed)


def test_player_disconnects_after_idle_timeout() -> None:
    async def run_test() -> None:
        voice = FakeVoiceClient()
        guild = SimpleNamespace(voice_client=voice)
        bot = SimpleNamespace(get_guild=lambda guild_id: guild)
        channel = FakeChannel()
        player = GuildPlayer(bot, 123, SimpleNamespace(), idle_timeout=0.01)
        player.text_channel = channel

        player._schedule_idle_disconnect()
        await asyncio.sleep(0.03)

        assert voice.disconnected
        assert channel.embeds[0].title == "Desconectado por inactividad"

    asyncio.run(run_test())


def test_new_activity_cancels_idle_disconnect() -> None:
    async def run_test() -> None:
        voice = FakeVoiceClient()
        guild = SimpleNamespace(voice_client=voice)
        bot = SimpleNamespace(get_guild=lambda guild_id: guild)
        player = GuildPlayer(bot, 123, SimpleNamespace(), idle_timeout=0.01)

        player._schedule_idle_disconnect()
        player._cancel_idle_disconnect()
        await asyncio.sleep(0.03)

        assert not voice.disconnected

    asyncio.run(run_test())
