"""Typed shape of the stored artwork names."""

from __future__ import annotations

from typing import TypedDict


class SamsungFrameArtworkNamesData(TypedDict):
    """Names given to the artworks of one TV, keyed by content id."""

    names: dict[str, str]
