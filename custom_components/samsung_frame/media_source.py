"""Expose the artworks of Reframed Gallery in the media browser."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, override

from homeassistant.components.media_player import BrowseError, MediaClass
from homeassistant.components.media_source import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
    Unresolvable,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, REFRAMED_NAME
from .data import ReframedArtwork
from .exceptions import ReframedGalleryError
from .reframed import ReframedGalleryClient

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import ReframedArtworkPage, ReframedFolder

RECENT = "recent"
COLLECTIONS = "collections"
COLLECTION = "collection"
ARTISTS = "artists"
ARTIST_INDEX = "artist-index"
ARTIST = "artist"
ARTWORK = "artwork"

_SLUG = re.compile(r"^[a-z0-9-]+$")
_PAGE = re.compile(r"^\d+$")
_FILE_PATH = re.compile(r"^[^/?#]+\.(?:jpe?g|png)$", re.IGNORECASE)


async def async_get_media_source(hass: HomeAssistant) -> SamsungFrameMediaSource:
    """Set up the Reframed Gallery media source."""
    return SamsungFrameMediaSource(ReframedGalleryClient(async_get_clientsession(hass)))


class SamsungFrameMediaSource(MediaSource):
    """
    Browse Reframed Gallery by recent additions, collection and artist.

    Every artwork resolves to its full-resolution image on the gallery CDN,
    so picking one in the ``upload_artwork`` action sends it straight to the
    TV. Identifiers are ``<kind>/<value>``; folders carry the slug the gallery
    uses in its URLs, artworks the CDN file name.
    """

    name: str = REFRAMED_NAME

    def __init__(self, client: ReframedGalleryClient) -> None:
        """Initialize the media source with the gallery client."""
        super().__init__(DOMAIN)
        self._client = client

    @override
    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Resolve an artwork to its full-resolution image."""
        kind, _, value = (item.identifier or "").partition("/")
        if kind != ARTWORK or not _FILE_PATH.match(value):
            msg = f"Unknown Reframed Gallery item: {item.identifier}"
            raise Unresolvable(msg)
        artwork = ReframedArtwork(file_path=value, title="", thumbnail_url="")
        return PlayMedia(artwork.image_url, artwork.mime_type)

    @override
    async def async_browse_media(self, item: MediaSourceItem) -> BrowseMediaSource:
        """Return the folder the identifier points at."""
        kind, _, value = (item.identifier or "").partition("/")
        try:
            return await self._async_browse(kind, value)
        except ReframedGalleryError as exception:
            raise BrowseError(str(exception)) from exception

    async def _async_browse(self, kind: str, value: str) -> BrowseMediaSource:
        if not kind:
            return _directory(
                None,
                REFRAMED_NAME,
                [
                    _directory(RECENT, "Recent"),
                    _directory(COLLECTIONS, "Collections"),
                    _directory(ARTISTS, "Artists"),
                ],
                media_class=MediaClass.APP,
            )
        handlers = {
            RECENT: (None, self._async_browse_recent),
            COLLECTIONS: (None, self._async_browse_collections),
            COLLECTION: (_SLUG, self._async_browse_collection),
            ARTISTS: (None, self._async_browse_artist_indexes),
            ARTIST_INDEX: (_PAGE, self._async_browse_artist_index),
            ARTIST: (_SLUG, self._async_browse_artist),
        }
        pattern, handler = handlers.get(kind, (None, None))
        valid_value = bool(pattern.match(value)) if pattern else not value
        if handler is None or not valid_value:
            msg = f"Unknown Reframed Gallery folder: {kind}/{value}"
            raise BrowseError(msg)
        return await handler(value)

    async def _async_browse_recent(self, _: str) -> BrowseMediaSource:
        page = await self._client.async_get_recent_artworks()
        return _artwork_directory(RECENT, page)

    async def _async_browse_collections(self, _: str) -> BrowseMediaSource:
        collections = await self._client.async_get_collections()
        return _directory(
            COLLECTIONS,
            "Collections",
            [_folder(COLLECTION, collection) for collection in collections],
        )

    async def _async_browse_collection(self, slug: str) -> BrowseMediaSource:
        page = await self._client.async_get_collection_artworks(slug)
        return _artwork_directory(f"{COLLECTION}/{slug}", page)

    async def _async_browse_artist_indexes(self, _: str) -> BrowseMediaSource:
        indexes = await self._client.async_get_artist_indexes()
        return _directory(
            ARTISTS,
            "Artists",
            [_folder(ARTIST_INDEX, index) for index in indexes],
        )

    async def _async_browse_artist_index(self, page: str) -> BrowseMediaSource:
        indexes = await self._client.async_get_artist_indexes()
        artists = await self._client.async_get_artists(page)
        return _directory(
            f"{ARTIST_INDEX}/{page}",
            next((index.title for index in indexes if index.slug == page), "Artists"),
            [_folder(ARTIST, artist) for artist in artists],
        )

    async def _async_browse_artist(self, slug: str) -> BrowseMediaSource:
        page = await self._client.async_get_artist_artworks(slug)
        return _artwork_directory(f"{ARTIST}/{slug}", page)


def _directory(
    identifier: str | None,
    title: str,
    children: list[BrowseMediaSource] | None = None,
    *,
    media_class: MediaClass = MediaClass.DIRECTORY,
    thumbnail: str | None = None,
) -> BrowseMediaSource:
    """Build a folder, with its children when they are already known."""
    return BrowseMediaSource(
        domain=DOMAIN,
        identifier=identifier,
        media_class=media_class,
        media_content_type="",
        title=title,
        can_play=False,
        can_expand=True,
        thumbnail=thumbnail,
        children=children,
        children_media_class=MediaClass.DIRECTORY if children else None,
    )


def _folder(kind: str, folder: ReframedFolder) -> BrowseMediaSource:
    """Build the entry of a gallery folder inside its parent."""
    return _directory(
        f"{kind}/{folder.slug}", folder.title, thumbnail=folder.thumbnail_url
    )


def _artwork_directory(identifier: str, page: ReframedArtworkPage) -> BrowseMediaSource:
    """Build a folder listing the artworks of a gallery page."""
    folder = _directory(
        identifier, page.title, [_artwork(artwork) for artwork in page.artworks]
    )
    folder.children_media_class = MediaClass.IMAGE
    return folder


def _artwork(artwork: ReframedArtwork) -> BrowseMediaSource:
    """Build the playable entry of an artwork."""
    return BrowseMediaSource(
        domain=DOMAIN,
        identifier=f"{ARTWORK}/{artwork.file_path}",
        media_class=MediaClass.IMAGE,
        media_content_type=artwork.mime_type,
        title=f"{artwork.title} ({artwork.artist})",
        can_play=True,
        can_expand=False,
        thumbnail=artwork.thumbnail_url,
    )
