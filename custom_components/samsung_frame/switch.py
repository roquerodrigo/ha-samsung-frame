"""Switch platform for samsung_frame."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.switch import SwitchEntity
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .entity import SamsungFrameEntity
from .exceptions import SamsungFrameApiClientError

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import SamsungFrameArtState, SamsungFrameConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: SamsungFrameConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    async_add_entities(
        [SamsungFrameArtModeSwitch(coordinator=entry.runtime_data.coordinator)],
    )


class SamsungFrameArtModeSwitch(SamsungFrameEntity, SwitchEntity):
    """Switch between art mode and regular TV content."""

    _attr_translation_key = "art_mode"

    @property
    def unique_id(self) -> str:
        """Return a unique id derived from the TV identifier."""
        return f"{self.device_id}_art_mode"

    @property
    def is_on(self) -> bool | None:
        """Return whether the TV is showing art."""
        data: SamsungFrameArtState | None = self.coordinator.data
        if data is None:
            return None
        return data["art_mode"]

    async def async_turn_on(self, **kwargs: bool) -> None:  # noqa: ARG002
        """Show art on the TV."""
        await self._async_set_art_mode(enabled=True)

    async def async_turn_off(self, **kwargs: bool) -> None:  # noqa: ARG002
        """Leave art mode."""
        await self._async_set_art_mode(enabled=False)

    async def _async_set_art_mode(self, *, enabled: bool) -> None:
        client = self.coordinator.config_entry.runtime_data.client
        try:
            await client.async_set_art_mode(enabled=enabled)
        except SamsungFrameApiClientError as exception:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="art_mode_failed",
            ) from exception
        data: SamsungFrameArtState | None = self.coordinator.data
        self.coordinator.async_set_updated_data(
            {
                "art_mode": enabled,
                "current_artwork_id": None
                if data is None
                else data["current_artwork_id"],
            }
        )
