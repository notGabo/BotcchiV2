from botcchi.services.spotify import SpotifyService


def test_parse_spotify_urls() -> None:
    assert SpotifyService.parse_url(
        "https://open.spotify.com/track/123ABC?si=test"
    ) == ("track", "123ABC")
    assert SpotifyService.parse_url(
        "https://open.spotify.com/intl-es/playlist/ABC123"
    ) == ("playlist", "ABC123")
    assert SpotifyService.parse_url("https://youtube.com/watch?v=123") is None
