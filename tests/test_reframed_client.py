from __future__ import annotations

import aiohttp
import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.samsung_frame.const import REFRAMED_USER_AGENT
from custom_components.samsung_frame.data import ReframedArtwork, ReframedFolder
from custom_components.samsung_frame.exceptions import ReframedGalleryError
from custom_components.samsung_frame.reframed import ReframedGalleryClient

from . import reframed_pages as pages

BASE = "https://www.reframed.gallery"


def _client(hass) -> ReframedGalleryClient:
    return ReframedGalleryClient(async_get_clientsession(hass))


async def test_recent_artworks(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE}/recent", text=pages.RECENT)
    page = await _client(hass).async_get_recent_artworks()
    assert page.title == "Recently Added"
    assert [artwork.title for artwork in page.artworks] == [
        "Impression, Sunrise",
        "The Gulf Stream",
    ]
    assert page.artworks[0] == ReframedArtwork(
        file_path=pages.MONET_SUNRISE,
        title="Impression, Sunrise",
        thumbnail_url=f"{pages.CDN}/originals/{pages.MONET_SUNRISE}",
    )


async def test_requests_identify_the_integration(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE}/recent", text=pages.RECENT)
    await _client(hass).async_get_recent_artworks()
    headers = aioclient_mock.mock_calls[0][3]
    assert headers["User-Agent"] == REFRAMED_USER_AGENT


async def test_pages_are_cached(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE}/recent", text=pages.RECENT)
    client = _client(hass)
    await client.async_get_recent_artworks()
    await client.async_get_recent_artworks()
    assert aioclient_mock.call_count == 1


async def test_cache_expires(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE}/recent", text=pages.RECENT)
    client = _client(hass)
    await client.async_get_recent_artworks()
    fetched_at, html = client._pages["/recent"]
    client._pages["/recent"] = (fetched_at - 3601, html)
    await client.async_get_recent_artworks()
    assert aioclient_mock.call_count == 2


async def test_missing_heading_falls_back(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE}/recent", text=pages.WITHOUT_HEADING)
    aioclient_mock.get(f"{BASE}/collections/in-bloom", text=pages.WITHOUT_HEADING)
    aioclient_mock.get(f"{BASE}/claude-monet", text=pages.WITHOUT_HEADING)
    client = _client(hass)
    assert (await client.async_get_recent_artworks()).title == "Recently Added"
    assert (await client.async_get_collection_artworks("in-bloom")).title == "in-bloom"
    assert (await client.async_get_artist_artworks("claude-monet")).title == (
        "claude-monet"
    )


async def test_collections(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE}/collections", text=pages.COLLECTIONS)
    collections = await _client(hass).async_get_collections()
    assert [collection.slug for collection in collections] == [
        "after-the-storm",
        "in-bloom",
    ]
    assert collections[0].title == "After the Storm"
    assert collections[0].thumbnail_url == f"{pages.CDN}/originals/{pages.HOMER_GULF}"


async def test_collection_artworks(hass, aioclient_mock):
    aioclient_mock.get(
        f"{BASE}/collections/after-the-storm", text=pages.AFTER_THE_STORM
    )
    page = await _client(hass).async_get_collection_artworks("after-the-storm")
    assert page.title == "After the Storm"
    assert [artwork.artist for artwork in page.artworks] == ["Winslow Homer"]


async def test_artist_indexes(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE}/artists", text=pages.ARTISTS_A_C)
    indexes = await _client(hass).async_get_artist_indexes()
    assert indexes == (
        ReframedFolder("1", "A to C", None),
        ReframedFolder("2", "D to F", None),
    )


async def test_artists_of_first_page(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE}/artists", text=pages.ARTISTS_A_C)
    artists = await _client(hass).async_get_artists("1")
    assert [(artist.slug, artist.title) for artist in artists] == [
        ("claude-monet", "Claude Monet")
    ]


async def test_artists_of_later_page(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE}/artists/page/2", text=pages.ARTISTS_D_F)
    artists = await _client(hass).async_get_artists("2")
    assert [artist.slug for artist in artists] == ["winslow-homer"]


async def test_artist_artworks_skip_other_artists(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE}/claude-monet", text=pages.MONET)
    page = await _client(hass).async_get_artist_artworks("claude-monet")
    assert page.title == "Claude Monet"
    assert [artwork.title for artwork in page.artworks] == [
        "Impression, Sunrise",
        "Wisteria",
    ]


async def test_http_error_raises(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE}/recent", status=503)
    with pytest.raises(ReframedGalleryError):
        await _client(hass).async_get_recent_artworks()


async def test_connection_error_raises(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE}/recent", exc=aiohttp.ClientConnectionError())
    with pytest.raises(ReframedGalleryError):
        await _client(hass).async_get_recent_artworks()


def test_artwork_properties():
    jpeg = ReframedArtwork(pages.MONET_SUNRISE, "Impression, Sunrise", "thumb")
    png = ReframedArtwork(pages.MONET_WISTERIA, "Wisteria", "thumb")
    assert jpeg.artist == "Claude Monet"
    assert jpeg.mime_type == "image/jpeg"
    assert png.mime_type == "image/png"
    assert jpeg.image_url == (
        f"https://cdn.reframed.gallery/originals/{pages.MONET_SUNRISE}"
    )
