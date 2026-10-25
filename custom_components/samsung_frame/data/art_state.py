"""Typed shape of the art mode state polled by the coordinator."""

from __future__ import annotations

from typing import TypedDict


class SamsungFrameArtState(TypedDict):
    """Art mode status and the artwork currently selected on the TV."""

    art_mode: bool
    current_artwork_id: str | None
