"""Keep a config entry bound to its TV when a firmware update changes its id."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import SamsungFrameConfigEntry, SamsungFrameDeviceInfo


class SamsungFrameDeviceIdentity:
    """
    Recognise the TV of a config entry across changes of its identifier.

    Firmware updates can replace the identifier the TV reports over REST, so
    the MAC address of the registered device decides whether a new identifier
    still belongs to the same TV.
    """

    def __init__(self, hass: HomeAssistant, entry: SamsungFrameConfigEntry) -> None:
        """Initialize for the TV ``entry`` was set up with."""
        self._hass = hass
        self._entry = entry

    @callback
    def is_same_tv(self, device_info: SamsungFrameDeviceInfo) -> bool:
        """Return whether ``device_info`` describes the TV of the entry."""
        if device_info["device_id"] == self._entry.unique_id:
            return True
        registered_mac = self._registered_mac()
        reported_mac = device_info["mac"]
        return (
            registered_mac is not None
            and reported_mac is not None
            and dr.format_mac(reported_mac) == registered_mac
        )

    @callback
    def async_adopt(self, device_info: SamsungFrameDeviceInfo) -> None:
        """Move the entry, its device and its entities to the current id."""
        previous_id = self._entry.unique_id
        current_id = device_info["device_id"]
        if previous_id is None or previous_id == current_id:
            return

        device_registry = dr.async_get(self._hass)
        device = device_registry.async_get_device_by_identifier(
            (DOMAIN, previous_id), self._entry.entry_id
        )
        if device is not None:
            device_registry.async_update_device(
                device.id, new_identifiers={(DOMAIN, current_id)}
            )

        entity_registry = er.async_get(self._hass)
        previous_prefix = f"{previous_id}_"
        for entity in er.async_entries_for_config_entry(
            entity_registry, self._entry.entry_id
        ):
            if entity.unique_id.startswith(previous_prefix):
                entity_registry.async_update_entity(
                    entity.entity_id,
                    new_unique_id=f"{current_id}_"
                    + entity.unique_id.removeprefix(previous_prefix),
                )

        self._hass.config_entries.async_update_entry(self._entry, unique_id=current_id)
        LOGGER.info(
            "The TV now identifies itself as %s instead of %s; moved %s to it",
            current_id,
            previous_id,
            self._entry.title,
        )

    def _registered_mac(self) -> str | None:
        device = dr.async_get(self._hass).async_get_device_by_identifier(
            (DOMAIN, self._entry.unique_id or ""), self._entry.entry_id
        )
        if device is None:
            return None
        return next(
            (
                value
                for connection_type, value in device.connections
                if connection_type == dr.CONNECTION_NETWORK_MAC
            ),
            None,
        )
