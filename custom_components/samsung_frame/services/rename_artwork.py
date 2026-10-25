"""Handler for the ``samsung_frame.rename_artwork`` action."""

from __future__ import annotations

from typing import TYPE_CHECKING

import probatio
from homeassistant.helpers import config_validation as cv

from .const import ATTR_CONFIG_ENTRY_ID, ATTR_CONTENT_ID, ATTR_NAME
from .loaded_entry import loaded_entry_data

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall

RENAME_ARTWORK_SCHEMA: probatio.Schema = probatio.Schema(
    {
        probatio.Required(ATTR_CONFIG_ENTRY_ID): cv.string,
        probatio.Required(ATTR_CONTENT_ID): cv.string,
        probatio.Required(ATTR_NAME): cv.string,
    },
)


class SamsungFrameRenameArtworkService:
    """Give an artwork of the TV the name Home Assistant shows for it."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Store the hass instance used to resolve the targeted entry."""
        self._hass = hass

    async def async_handle(self, call: ServiceCall) -> None:
        """Store the name, or forget it when the new name is blank."""
        data = loaded_entry_data(self._hass, call.data[ATTR_CONFIG_ENTRY_ID])
        content_id: str = call.data[ATTR_CONTENT_ID]
        name: str = call.data[ATTR_NAME].strip()
        if name:
            await data.artwork_names.async_set(content_id, name)
        else:
            await data.artwork_names.async_remove(content_id)
        data.coordinator.async_update_listeners()
