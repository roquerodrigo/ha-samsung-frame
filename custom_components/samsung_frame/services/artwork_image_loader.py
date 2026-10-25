"""Turn the image an action points at into bytes the TV accepts."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import aiohttp
from homeassistant.components import media_source
from homeassistant.components.media_player.browse_media import (
    async_process_play_media_url,
)
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from ..const import DOMAIN, DOWNLOAD_TIMEOUT_SECONDS
from ..data import SamsungFrameArtworkImage

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_JPEG_SIGNATURE = b"\xff\xd8\xff"
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_DOWNLOADABLE_SCHEMES: tuple[str, ...] = ("http://", "https://")


class SamsungFrameArtworkImageLoader:
    """
    Load an image from a media source or a URL.

    Local media resolves straight to a file on disk; any other media source
    (image entities, for example) resolves to a URL served by Home Assistant
    itself, which is downloaded like a plain URL would be.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        """Store the hass instance used to resolve and download media."""
        self._hass = hass

    async def async_load(self, media_content_id: str) -> SamsungFrameArtworkImage:
        """Return the image bytes together with the file type the TV expects."""
        content = await self._async_read(media_content_id)
        if content.startswith(_JPEG_SIGNATURE):
            return SamsungFrameArtworkImage(content=content, file_type="jpg")
        if content.startswith(_PNG_SIGNATURE):
            return SamsungFrameArtworkImage(content=content, file_type="png")
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="unsupported_image_format",
        )

    async def _async_read(self, media_content_id: str) -> bytes:
        if not media_source.is_media_source_id(media_content_id):
            if not media_content_id.startswith(_DOWNLOADABLE_SCHEMES):
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="unsupported_image_source",
                    translation_placeholders={"media_content_id": media_content_id},
                )
            return await self._async_download(media_content_id)

        try:
            play_media = await media_source.async_resolve_media(
                self._hass, media_content_id, None
            )
        except media_source.Unresolvable as exception:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="image_not_resolved",
                translation_placeholders={"media_content_id": media_content_id},
            ) from exception

        if play_media.path is not None:
            return await self._hass.async_add_executor_job(play_media.path.read_bytes)
        return await self._async_download(
            async_process_play_media_url(self._hass, play_media.url)
        )

    async def _async_download(self, url: str) -> bytes:
        session = async_get_clientsession(self._hass)
        try:
            async with (
                asyncio.timeout(DOWNLOAD_TIMEOUT_SECONDS),
                session.get(url) as response,
            ):
                response.raise_for_status()
                return await response.read()
        except (TimeoutError, aiohttp.ClientError) as exception:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="image_download_failed",
            ) from exception
