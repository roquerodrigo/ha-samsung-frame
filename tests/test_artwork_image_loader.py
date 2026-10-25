from __future__ import annotations

from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
from homeassistant.components.media_source import PlayMedia, Unresolvable
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from custom_components.samsung_frame.services.artwork_image_loader import (
    SamsungFrameArtworkImageLoader,
)

JPEG = b"\xff\xd8\xff\xe0jpeg-body"
PNG = b"\x89PNG\r\n\x1a\npng-body"
MODULE = "custom_components.samsung_frame.services.artwork_image_loader"
LOCAL_MEDIA_ID = "media-source://media_source/local/frame.jpg"
IMAGE_ENTITY_ID = "media-source://image/image.living_room"


def _resolve_to(play_media):
    return patch(
        f"{MODULE}.media_source.async_resolve_media",
        AsyncMock(return_value=play_media),
    )


async def test_local_media_is_read_from_disk(hass, tmp_path):
    image_path = tmp_path / "frame.jpg"
    image_path.write_bytes(JPEG)
    play_media = PlayMedia("/media/local/frame.jpg", "image/jpeg", path=image_path)
    with _resolve_to(play_media):
        image = await SamsungFrameArtworkImageLoader(hass).async_load(LOCAL_MEDIA_ID)
    assert image.content == JPEG
    assert image.file_type == "jpg"


async def test_media_without_path_is_downloaded(hass, aioclient_mock):
    aioclient_mock.get("http://ha.local/api/image_proxy/image.living_room", content=PNG)
    play_media = PlayMedia("/api/image_proxy/image.living_room", "image/png")
    with (
        _resolve_to(play_media),
        patch(
            f"{MODULE}.async_process_play_media_url",
            return_value="http://ha.local/api/image_proxy/image.living_room",
        ),
    ):
        image = await SamsungFrameArtworkImageLoader(hass).async_load(IMAGE_ENTITY_ID)
    assert image.content == PNG
    assert image.file_type == "png"


async def test_plain_url_is_downloaded(hass, aioclient_mock):
    aioclient_mock.get("https://example.com/art.jpg", content=JPEG)
    image = await SamsungFrameArtworkImageLoader(hass).async_load(
        "https://example.com/art.jpg"
    )
    assert image.file_type == "jpg"


async def test_failed_download_raises(hass, aioclient_mock):
    aioclient_mock.get("https://example.com/art.jpg", status=404)
    with pytest.raises(HomeAssistantError) as error:
        await SamsungFrameArtworkImageLoader(hass).async_load(
            "https://example.com/art.jpg"
        )
    assert error.value.translation_key == "image_download_failed"


async def test_download_connection_error_raises(hass, aioclient_mock):
    aioclient_mock.get(
        "https://example.com/art.jpg", exc=aiohttp.ClientConnectionError()
    )
    with pytest.raises(HomeAssistantError) as error:
        await SamsungFrameArtworkImageLoader(hass).async_load(
            "https://example.com/art.jpg"
        )
    assert error.value.translation_key == "image_download_failed"


async def test_unknown_source_is_rejected(hass):
    with pytest.raises(ServiceValidationError) as error:
        await SamsungFrameArtworkImageLoader(hass).async_load("/config/www/art.jpg")
    assert error.value.translation_key == "unsupported_image_source"


async def test_unresolvable_media_is_rejected(hass):
    with (
        patch(
            f"{MODULE}.media_source.async_resolve_media",
            AsyncMock(side_effect=Unresolvable("gone")),
        ),
        pytest.raises(ServiceValidationError) as error,
    ):
        await SamsungFrameArtworkImageLoader(hass).async_load(LOCAL_MEDIA_ID)
    assert error.value.translation_key == "image_not_resolved"


async def test_non_image_content_is_rejected(hass, aioclient_mock):
    aioclient_mock.get("https://example.com/art.gif", content=b"GIF89a")
    with pytest.raises(ServiceValidationError) as error:
        await SamsungFrameArtworkImageLoader(hass).async_load(
            "https://example.com/art.gif"
        )
    assert error.value.translation_key == "unsupported_image_format"
