"""Client for the public pages of Reframed Gallery."""

from __future__ import annotations

import asyncio
import re
import time
from typing import TYPE_CHECKING

import aiohttp

from ..const import (
    LOGGER,
    REFRAMED_BASE_URL,
    REFRAMED_PAGE_CACHE_SECONDS,
    REFRAMED_REQUEST_TIMEOUT_SECONDS,
    REFRAMED_USER_AGENT,
)
from ..data import ReframedArtwork, ReframedArtworkPage, ReframedFolder
from ..exceptions import ReframedGalleryError
from .link_parser import ReframedLinkParser
from .page_parser import ReframedPageParser

if TYPE_CHECKING:
    from collections.abc import Iterable

    from ..data import ReframedTile

_ARTWORK_PATH = re.compile(r"^/(?!collections/|artists/)[a-z0-9-]+/[a-z0-9-]+$")
_ARTIST_PATH = re.compile(r"^/([a-z0-9-]+)$")
_COLLECTION_PATH = re.compile(r"^/collections/([a-z0-9-]+)$")
_ARTIST_INDEX_PATH = re.compile(r"^/artists(?:/page/(\d+))?$")
_ORIGINAL_FILE = re.compile(r"/originals/([^/?#]+\.(?:jpe?g|png))$", re.IGNORECASE)
_RESERVED_ARTIST_SLUGS: frozenset[str] = frozenset(
    {"artists", "collections", "recent", "verticals", "colors"}
)


class ReframedGalleryClient:
    """
    Read artworks, artists and collections from Reframed Gallery.

    The gallery has no public API (``robots.txt`` disallows ``/api/``), so
    the client reads the same HTML pages a visitor sees. Every page is cached
    for an hour: browsing back and forth in the media browser must not turn
    into a stream of requests to a site run by a single person.
    """

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize the client with the shared HTTP session."""
        self._session = session
        self._pages: dict[str, tuple[float, str]] = {}
        self._lock = asyncio.Lock()

    async def async_get_recent_artworks(self) -> ReframedArtworkPage:
        """Return the artworks most recently added to the gallery."""
        parser = await self._async_parse("/recent")
        return ReframedArtworkPage(
            title=parser.heading or "Recently Added",
            artworks=_artworks(parser.tiles),
        )

    async def async_get_collections(self) -> tuple[ReframedFolder, ...]:
        """Return the curated collections."""
        parser = await self._async_parse("/collections")
        return _folders(parser.tiles, _COLLECTION_PATH)

    async def async_get_collection_artworks(self, slug: str) -> ReframedArtworkPage:
        """Return the artworks of a collection."""
        parser = await self._async_parse(f"/collections/{slug}")
        return ReframedArtworkPage(
            title=parser.heading or slug,
            artworks=_artworks(parser.tiles),
        )

    async def async_get_artist_indexes(self) -> tuple[ReframedFolder, ...]:
        """Return the alphabetical pages the artist list is split into."""
        parser = ReframedLinkParser()
        parser.feed(await self._async_page("/artists"))
        indexes: dict[str, ReframedFolder] = {}
        for path, text in parser.links:
            match = _ARTIST_INDEX_PATH.match(path)
            if match is None or not text:
                continue
            page = match.group(1) or "1"
            indexes.setdefault(page, ReframedFolder(page, text, None))
        return tuple(indexes.values())

    async def async_get_artists(self, page: str) -> tuple[ReframedFolder, ...]:
        """Return the artists listed on one alphabetical page."""
        path = "/artists" if page == "1" else f"/artists/page/{page}"
        artists = _folders((await self._async_parse(path)).tiles, _ARTIST_PATH)
        return tuple(
            artist for artist in artists if artist.slug not in _RESERVED_ARTIST_SLUGS
        )

    async def async_get_artist_artworks(self, slug: str) -> ReframedArtworkPage:
        """Return the artworks of an artist."""
        parser = await self._async_parse(f"/{slug}")
        return ReframedArtworkPage(
            title=parser.heading or slug,
            artworks=_artworks(
                tile for tile in parser.tiles if tile.path.startswith(f"/{slug}/")
            ),
        )

    async def _async_parse(self, path: str) -> ReframedPageParser:
        parser = ReframedPageParser()
        parser.feed(await self._async_page(path))
        return parser

    async def _async_page(self, path: str) -> str:
        async with self._lock:
            cached = self._pages.get(path)
            if cached is not None and time.monotonic() - cached[0] < (
                REFRAMED_PAGE_CACHE_SECONDS
            ):
                return cached[1]
            html = await self._async_download(path)
            self._pages[path] = (time.monotonic(), html)
            return html

    async def _async_download(self, path: str) -> str:
        LOGGER.debug("Fetching Reframed Gallery page %s", path)
        try:
            async with (
                asyncio.timeout(REFRAMED_REQUEST_TIMEOUT_SECONDS),
                self._session.get(
                    f"{REFRAMED_BASE_URL}{path}",
                    headers={"User-Agent": REFRAMED_USER_AGENT},
                ) as response,
            ):
                response.raise_for_status()
                return await response.text()
        except (TimeoutError, aiohttp.ClientError) as exception:
            msg = f"Failed to fetch the Reframed Gallery page {path}: {exception}"
            raise ReframedGalleryError(msg) from exception


def _artworks(tiles: Iterable[ReframedTile]) -> tuple[ReframedArtwork, ...]:
    """Turn artwork tiles into artworks, keeping page order and dropping repeats."""
    artworks: dict[str, ReframedArtwork] = {}
    for tile in tiles:
        file_match = _ORIGINAL_FILE.search(tile.image_source)
        if not _ARTWORK_PATH.match(tile.path) or file_match is None:
            continue
        file_path = file_match.group(1)
        artworks.setdefault(
            file_path,
            ReframedArtwork(
                file_path=file_path,
                title=tile.title,
                thumbnail_url=tile.image_source,
            ),
        )
    return tuple(artworks.values())


def _folders(
    tiles: Iterable[ReframedTile], path_pattern: re.Pattern[str]
) -> tuple[ReframedFolder, ...]:
    """Turn the tiles whose link matches ``path_pattern`` into folders."""
    folders: dict[str, ReframedFolder] = {}
    for tile in tiles:
        match = path_pattern.match(tile.path)
        if match is None:
            continue
        slug = match.group(1)
        folders.setdefault(slug, ReframedFolder(slug, tile.title, tile.image_source))
    return tuple(folders.values())
