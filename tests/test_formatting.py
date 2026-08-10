from botcchi.utils.formatting import format_duration, truncate


def test_format_duration() -> None:
    assert format_duration(222) == "3:42"
    assert format_duration(3661) == "1:01:01"
    assert format_duration(None) == "Desconocida"


def test_truncate() -> None:
    assert truncate("Botcchi", 20) == "Botcchi"
    assert truncate("Botcchi", 6) == "Bot..."
