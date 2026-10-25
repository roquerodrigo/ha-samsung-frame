"""Sensor platform for samsung_frame."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity

from .entity import SamsungFrameEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import SamsungFrameArtState, SamsungFrameConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: SamsungFrameConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities(
        [SamsungFrameCurrentArtworkSensor(coordinator=entry.runtime_data.coordinator)],
    )


class SamsungFrameCurrentArtworkSensor(SamsungFrameEntity, SensorEntity):
    """Artwork currently selected on the TV."""

    _attr_translation_key = "current_artwork"

    @property
    def unique_id(self) -> str:
        """Return a unique id derived from the TV identifier."""
        return f"{self.device_id}_current_artwork"

    @property
    def native_value(self) -> str | None:
        """Return the name of the selected artwork, or its id when it has none."""
        content_id = self._content_id
        if content_id is None:
            return None
        names = self.coordinator.config_entry.runtime_data.artwork_names
        return names.get(content_id) or content_id

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        """Return the content id the actions expect."""
        return {"content_id": self._content_id}

    @property
    def _content_id(self) -> str | None:
        data: SamsungFrameArtState | None = self.coordinator.data
        if data is None:
            return None
        return data["current_artwork_id"]
