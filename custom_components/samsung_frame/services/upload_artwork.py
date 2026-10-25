"""Handler for the ``samsung_frame.upload_artwork`` action."""

from __future__ import annotations

from typing import TYPE_CHECKING

import probatio
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import selector

from ..const import DOMAIN
from ..exceptions import SamsungFrameApiClientError
from .artwork_image_loader import SamsungFrameArtworkImageLoader
from .artwork_name import suggested_artwork_name
from .const import (
    ATTR_CONFIG_ENTRY_ID,
    ATTR_CONTENT_ID,
    ATTR_IMAGE,
    ATTR_MATTE_COLOR,
    ATTR_MATTE_STYLE,
    ATTR_NAME,
    ATTR_SHOW,
    MATTE_COLORS,
    MATTE_STYLE_NONE,
    MATTE_STYLES,
)
from .loaded_entry import loaded_entry_data

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse

UPLOAD_ARTWORK_SCHEMA: probatio.Schema = probatio.Schema(
    {
        probatio.Required(ATTR_CONFIG_ENTRY_ID): cv.string,
        probatio.Required(ATTR_IMAGE): selector.MediaSelector(
            selector.MediaSelectorConfig(accept=["image/*"]),
        ),
        probatio.Optional(ATTR_MATTE_STYLE, default=MATTE_STYLE_NONE): probatio.In(
            MATTE_STYLES
        ),
        probatio.Optional(ATTR_MATTE_COLOR, default=MATTE_COLORS[0]): probatio.In(
            MATTE_COLORS
        ),
        probatio.Optional(ATTR_SHOW, default=True): cv.boolean,
        probatio.Optional(ATTR_NAME): cv.string,
    },
)


class SamsungFrameUploadArtworkService:
    """Upload an image to the art collection of the TV."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Store the hass instance used to resolve the entry and the image."""
        self._hass = hass
        self._image_loader = SamsungFrameArtworkImageLoader(hass)

    async def async_handle(self, call: ServiceCall) -> ServiceResponse:
        """Upload and name the image, optionally show it, and return its id."""
        data = loaded_entry_data(self._hass, call.data[ATTR_CONFIG_ENTRY_ID])
        media_content_id: str = call.data[ATTR_IMAGE]["media_content_id"]
        image = await self._image_loader.async_load(media_content_id)
        try:
            content_id = await data.client.async_upload_artwork(
                image,
                _matte_id(call.data[ATTR_MATTE_STYLE], call.data[ATTR_MATTE_COLOR]),
                show=call.data[ATTR_SHOW],
            )
        except SamsungFrameApiClientError as exception:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="upload_failed",
            ) from exception
        name = call.data.get(ATTR_NAME) or suggested_artwork_name(
            media_content_id,
            call.data[ATTR_IMAGE].get("metadata", {}).get("title"),
        )
        if name:
            await data.artwork_names.async_set(content_id, name)
        await data.coordinator.async_request_refresh()
        if not call.return_response:
            return None
        return {ATTR_CONTENT_ID: content_id, ATTR_NAME: name}


def _matte_id(style: str, color: str) -> str:
    """Combine the style and color into the matte id the TV understands."""
    if style == MATTE_STYLE_NONE:
        return MATTE_STYLE_NONE
    return f"{style}_{color}"
