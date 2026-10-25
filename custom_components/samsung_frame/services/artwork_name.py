"""Suggest a name for an uploaded artwork from the media it came from."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from urllib.parse import unquote, urlsplit

from ..const import DOMAIN

_REFRAMED_ARTWORK_PREFIX = f"media-source://{DOMAIN}/artwork/"
_REFRAMED_SUFFIX = re.compile(r" - reframed(?:-\d+)?$", re.IGNORECASE)


def suggested_artwork_name(media_content_id: str, title: str | None) -> str | None:
    """
    Return the name to give an artwork when the user did not pick one.

    The media browser hands over the title it displayed, which is the best
    name. Without it (actions written in YAML), the name comes from the file
    name: Reframed Gallery files read ``Artist - Title - reframed.jpg``, any
    other file contributes its name without the extension.
    """
    if title and title.strip():
        return title.strip()
    stem = PurePosixPath(unquote(urlsplit(media_content_id).path)).stem.strip()
    if media_content_id.startswith(_REFRAMED_ARTWORK_PREFIX):
        artist, separator, artwork = _REFRAMED_SUFFIX.sub("", stem).partition(" - ")
        if separator:
            return f"{artwork} ({artist})"
    return stem or None
