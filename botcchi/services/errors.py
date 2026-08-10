class MusicError(Exception):
    """Base exception for user-facing music errors."""


class MediaExtractionError(MusicError):
    """Raised when a provider cannot resolve media."""


class SpotifyNotConfiguredError(MusicError):
    """Raised when Spotify credentials are not available."""


class VoiceChannelError(MusicError):
    """Raised when a voice-channel operation is invalid."""
