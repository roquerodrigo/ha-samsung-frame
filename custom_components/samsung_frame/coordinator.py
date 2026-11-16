"""DataUpdateCoordinator for samsung_frame."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, LOGGER
from .exceptions import (
    SamsungFrameApiClientAuthenticationError,
    SamsungFrameApiClientError,
)

if TYPE_CHECKING:
    from datetime import timedelta

    from homeassistant.core import HomeAssistant

    from .data import SamsungFrameArtState, SamsungFrameConfigEntry


class SamsungFrameDataUpdateCoordinator(DataUpdateCoordinator["SamsungFrameArtState"]):
    """Coordinator polling the art mode state of the TV."""

    config_entry: SamsungFrameConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        scan_interval: timedelta,
        config_entry: SamsungFrameConfigEntry,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=scan_interval,
            always_update=False,
            config_entry=config_entry,
        )

    async def _async_update_data(self) -> SamsungFrameArtState:
        """Fetch the art mode state from the TV."""
        client = self.config_entry.runtime_data.client
        try:
            art_state = await client.async_get_art_state()
        except SamsungFrameApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except SamsungFrameApiClientError as exception:
            raise UpdateFailed(exception) from exception
        self._async_forget_revoked_token(client.token)
        return art_state

    def _async_forget_revoked_token(self, token: str | None) -> None:
        """
        Stop storing a token the TV revoked.

        Presenting a revoked token makes the TV revoke the one the core Samsung
        TV integration holds as well, so both would need approval on every start.
        """
        if self.config_entry.data["token"] == token:
            return
        self.hass.config_entries.async_update_entry(
            self.config_entry, data={**self.config_entry.data, "token": token}
        )
