"""SamsungFrameEntity base class."""

from __future__ import annotations

from homeassistant.helpers.device_registry import (
    CONNECTION_NETWORK_MAC,
    DeviceInfo,
    format_mac,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import SamsungFrameDataUpdateCoordinator


class SamsungFrameEntity(CoordinatorEntity[SamsungFrameDataUpdateCoordinator]):
    """Base entity for Samsung The Frame."""

    _attr_has_entity_name = True

    @property
    def device_id(self) -> str:
        """Return the identifier the TV reports for itself."""
        return self.coordinator.config_entry.runtime_data.device_info["device_id"]

    @property
    def device_info(self) -> DeviceInfo:
        """Return the TV as the device."""
        device = self.coordinator.config_entry.runtime_data.device_info
        mac = device["mac"]
        return DeviceInfo(
            identifiers={(DOMAIN, device["device_id"])},
            connections={(CONNECTION_NETWORK_MAC, format_mac(mac))} if mac else set(),
            name=device["name"],
            manufacturer=MANUFACTURER,
            model=device["model_name"],
        )
