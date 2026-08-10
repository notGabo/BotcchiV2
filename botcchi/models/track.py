from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Requester:
    display_name: str
    avatar_url: str | None = None


@dataclass(frozen=True, slots=True)
class Track:
    title: str
    webpage_url: str
    playback_query: str
    requester: Requester
    duration: int | None = None
    uploader: str = "Desconocido"
    thumbnail: str | None = None
    source: str = "youtube"

    @property
    def display_title(self) -> str:
        return self.title or "Titulo desconocido"
