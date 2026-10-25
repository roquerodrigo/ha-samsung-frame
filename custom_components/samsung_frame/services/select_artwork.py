"""Handler for the ``samsung_frame.select_artwork`` action."""

from __future__ import annotations

from typing import TYPE_CHECKING

import probatio
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from ..const import DOMAIN
from ..exceptions import SamsungFrameApiClientError
from .const import ATTR_CONFIG_ENTRY_ID, ATTR_CONTENT_ID, ATTR_SHOW
from .loaded_entry import loaded_entry_data

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall

SELECT_ARTWORK_SCHEMA: probatio.Schema = probatio.Schema(
    {
        probatio.Required(ATTR_CONFIG_ENTRY_ID): cv.string,
        probatio.Required(ATTR_CONTENT_ID): cv.string,
        probatio.Optional(ATTR_SHOW, default=True): cv.boolean,
    },
)


class SamsungFrameSelectArtworkService:
    """Select an artwork that is already in the collection of the TV."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Store the hass instance used to resolve the targeted entry."""
        self._hass = hass

    async def async_handle(self, call: ServiceCall) -> None:
        """Select the artwork and refresh the state."""
        data = loaded_entry_data(self._hass, call.data[ATTR_CONFIG_ENTRY_ID])
        content_id: str = call.data[ATTR_CONTENT_ID]
        try:
            await data.client.async_select_artwork(
                content_id, show=call.data[ATTR_SHOW]
            )
        except SamsungFrameApiClientError as exception:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="select_failed",
                translation_placeholders={"content_id": content_id},
            ) from exception
        await data.coordinator.async_request_refresh()
