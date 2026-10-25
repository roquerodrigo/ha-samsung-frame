"""Error raised when Reframed Gallery cannot be read."""

from __future__ import annotations


class ReframedGalleryError(Exception):
    """Exception to indicate a gallery page could not be fetched or parsed."""
