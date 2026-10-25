from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.media_player import BrowseError, MediaClass
from homeassistant.components.media_source import (
    MediaSourceItem,
    Unresolvable,
    async_browse_media,
    async_resolve_media,
)

from custom_components.samsung_frame.const import DOMAIN
from custom_components.samsung_frame.data import (
    ReframedArtwork,
    ReframedArtworkPage,
    ReframedFolder,
)
from custom_components.samsung_frame.exceptions import ReframedGalleryError
from custom_components.samsung_frame.media_source import (
    SamsungFrameMediaSource,
    async_get_media_source,
)

from . import reframed_pages as pages

SUNRISE = ReframedArtwork(pages.MONET_SUNRISE, "Impression, Sunrise", "thumb-sunrise")
PAGE = ReframedArtworkPage(title="Claude Monet", artworks=(SUNRISE,))


@pytest.fixture
def client():
    gallery = MagicMock()
    gallery.async_get_recent_artworks = AsyncMock(
        return_value=ReframedArtworkPage("Recently Added", (SUNRISE,))
    )
    gallery.async_get_collections = AsyncMock(
        return_value=(ReframedFolder("in-bloom", "In Bloom", "thumb-bloom"),)
    )
    gallery.async_get_collection_artworks = AsyncMock(
        return_value=ReframedArtworkPage("In Bloom", (SUNRISE,))
    )
    gallery.async_get_artist_indexes = AsyncMock(
        return_value=(ReframedFolder("1", "A to C", None),)
    )
    gallery.async_get_artists = AsyncMock(
        return_value=(ReframedFolder("claude-monet", "Claude Monet", "thumb"),)
    )
    gallery.async_get_artist_artworks = AsyncMock(return_value=PAGE)
    return gallery


def _item(hass, identifier):
    return MediaSourceItem(hass, DOMAIN, identifier, None)


async def _browse(hass, client, identifier):
    return await SamsungFrameMediaSource(client).async_browse_media(
        _item(hass, identifier)
    )


async def test_root_lists_the_sections(hass, client):
    root = await _browse(hass, client, None)
    assert root.title == "Reframed Gallery"
    assert root.media_class == MediaClass.APP
    assert [(child.identifier, child.title) for child in root.children] == [
        ("recent", "Recent"),
        ("collections", "Collections"),
        ("artists", "Artists"),
    ]


async def test_recent_lists_playable_artworks(hass, client):
    folder = await _browse(hass, client, "recent")
    assert folder.title == "Recently Added"
    assert folder.children_media_class == MediaClass.IMAGE
    artwork = folder.children[0]
    assert artwork.identifier == f"artwork/{pages.MONET_SUNRISE}"
    assert artwork.title == "Impression, Sunrise (Claude Monet)"
    assert artwork.media_content_type == "image/jpeg"
    assert artwork.thumbnail == "thumb-sunrise"
    assert artwork.can_play
    assert not artwork.can_expand


async def test_collections_and_collection(hass, client):
    collections = await _browse(hass, client, "collections")
    assert [
        (child.identifier, child.title, child.thumbnail)
        for child in collections.children
    ] == [("collection/in-bloom", "In Bloom", "thumb-bloom")]
    collection = await _browse(hass, client, "collection/in-bloom")
    client.async_get_collection_artworks.assert_awaited_once_with("in-bloom")
    assert collection.title == "In Bloom"
    assert len(collection.children) == 1


async def test_artists_drill_down(hass, client):
    indexes = await _browse(hass, client, "artists")
    assert indexes.children[0].identifier == "artist-index/1"
    assert indexes.children[0].title == "A to C"
    artists = await _browse(hass, client, "artist-index/1")
    client.async_get_artists.assert_awaited_once_with("1")
    assert artists.title == "A to C"
    assert artists.children[0].identifier == "artist/claude-monet"
    artist = await _browse(hass, client, "artist/claude-monet")
    client.async_get_artist_artworks.assert_awaited_once_with("claude-monet")
    assert artist.title == "Claude Monet"


@pytest.mark.parametrize(
    "identifier",
    [
        "unknown",
        "recent/extra",
        "collection/../etc",
        "collection/",
        "artist-index/a",
        "artist/Claude Monet",
    ],
)
async def test_unknown_folders_raise(hass, client, identifier):
    with pytest.raises(BrowseError):
        await _browse(hass, client, identifier)


async def test_artist_index_missing_from_the_tabs_keeps_a_generic_title(hass, client):
    artists = await _browse(hass, client, "artist-index/9")
    assert artists.title == "Artists"


async def test_gallery_errors_become_browse_errors(hass, client):
    client.async_get_recent_artworks.side_effect = ReframedGalleryError("down")
    with pytest.raises(BrowseError):
        await _browse(hass, client, "recent")


async def test_resolve_artwork_to_original(hass, client):
    play_media = await SamsungFrameMediaSource(client).async_resolve_media(
        _item(hass, f"artwork/{pages.MONET_WISTERIA}")
    )
    assert play_media.url == (
        f"https://cdn.reframed.gallery/originals/{pages.MONET_WISTERIA}"
    )
    assert play_media.mime_type == "image/png"


@pytest.mark.parametrize(
    "identifier",
    [
        None,
        "recent",
        "artwork/",
        "artwork/a/b.jpg",
        "artwork/notes.txt",
        "artwork/x.jpg?y",
    ],
)
async def test_resolve_rejects_anything_else(hass, client, identifier):
    with pytest.raises(Unresolvable):
        await SamsungFrameMediaSource(client).async_resolve_media(
            _item(hass, identifier)
        )


async def test_media_source_registered_with_the_integration(
    hass, setup_integration, aioclient_mock
):
    aioclient_mock.get("https://www.reframed.gallery/recent", text=pages.RECENT)
    source = await async_get_media_source(hass)
    assert isinstance(source, SamsungFrameMediaSource)
    folder = await async_browse_media(hass, f"media-source://{DOMAIN}/recent")
    assert folder.title == "Recently Added"
    play_media = await async_resolve_media(
        hass, f"media-source://{DOMAIN}/artwork/{pages.HOMER_GULF}", None
    )
    assert play_media.url.endswith(pages.HOMER_GULF)
