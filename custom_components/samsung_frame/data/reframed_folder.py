"""Browsable group of Reframed Gallery: a collection, an artist or an index page."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReframedFolder:
    """Slug and caption of a browsable group, with its cover image when it has one."""

    slug: str
    title: str
    thumbnail_url: str | None
