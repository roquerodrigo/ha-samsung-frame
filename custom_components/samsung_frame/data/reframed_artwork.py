"""Artwork offered by Reframed Gallery."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import unquote

REFRAMED_ORIGINALS_URL = "https://cdn.reframed.gallery/originals/"


@dataclass(frozen=True)
class ReframedArtwork:
    """
    Artwork of the gallery, identified by its file on the CDN.

    ``file_path`` stays percent-encoded exactly as the CDN serves it, so it
    can travel inside a media source identifier and be appended to the CDN
    URL without re-encoding.
    """

    file_path: str
    title: str
    thumbnail_url: str

    @property
    def artist(self) -> str:
        """Return the artist, which the gallery puts before the title in file names."""
        return unquote(self.file_path).split(" - ", 1)[0]

    @property
    def image_url(self) -> str:
        """Return the full-resolution image on the CDN."""
        return f"{REFRAMED_ORIGINALS_URL}{self.file_path}"

    @property
    def mime_type(self) -> str:
        """Return the MIME type implied by the file extension."""
        if self.file_path.lower().endswith(".png"):
            return "image/png"
        return "image/jpeg"
