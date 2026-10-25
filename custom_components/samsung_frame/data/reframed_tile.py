"""Linked image tile scraped from a Reframed Gallery page."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReframedTile:
    """Link target, caption and image of one tile on a gallery page."""

    path: str
    title: str
    image_source: str
