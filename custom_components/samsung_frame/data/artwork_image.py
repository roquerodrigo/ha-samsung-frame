"""Image ready to be uploaded to the TV."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SamsungFrameArtworkImage:
    """Raw image bytes and the file type the TV expects for them."""

    content: bytes
    file_type: str
