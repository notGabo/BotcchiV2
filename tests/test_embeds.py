from botcchi.models import Requester, Track
from botcchi.ui.embeds import now_playing_embed


def test_now_playing_embed_matches_reference_layout() -> None:
    track = Track(
        title="FLOW - Colors",
        webpage_url="https://www.youtube.com/watch?v=example",
        playback_query="https://www.youtube.com/watch?v=example",
        requester=Requester("nafle"),
        duration=222,
        uploader="FLOW Official YouTube Channel",
        thumbnail="https://i.ytimg.com/vi/example/hqdefault.jpg",
    )

    embed = now_playing_embed(track)

    assert embed.title == "Reproduciendo"
    assert embed.description == "[FLOW - Colors](https://www.youtube.com/watch?v=example)"
    assert embed.color.value == 0x00FF23
    assert embed.thumbnail.url == track.thumbnail
    assert [(field.name, field.value) for field in embed.fields] == [
        ("Duración", "3:42"),
        ("Subido por", "FLOW Official YouTube Channel"),
        ("Pedido por", "nafle"),
    ]
    assert embed.footer.text == (
        "Se ha añadido la canción a la cola: FLOW - Colors - "
        "FLOW Official YouTube Channel (3:42)"
    )
