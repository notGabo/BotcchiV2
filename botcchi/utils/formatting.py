from __future__ import annotations


def format_duration(seconds: int | None) -> str:
    if seconds is None or seconds < 0:
        return "Desconocida"

    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def truncate(value: str, limit: int, suffix: str = "...") -> str:
    if len(value) <= limit:
        return value
    return value[: max(0, limit - len(suffix))].rstrip() + suffix
