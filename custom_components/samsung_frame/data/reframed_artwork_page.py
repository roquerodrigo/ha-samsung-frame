"""Gallery page listing artworks: recent additions, a collection or an artist."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .reframed_artwork import ReframedArtwork


@dataclass(frozen=True)
class ReframedArtworkPage:
    """Heading of the page and the artworks it lists, in page order."""

    title: str
    artworks: tuple[ReframedArtwork, ...]
