"""Samsung The Frame integration for Home Assistant."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, cast

from homeassistant.const import CONF_SCAN_INTERVAL, Platform
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.loader import async_get_loaded_integration

from .api import SamsungFrameApiClient
from .artwork_names import SamsungFrameArtworkNames
from .const import DEFAULT_SCAN_INTERVAL_SECONDS, DOMAIN
from .coordinator import SamsungFrameDataUpdateCoordinator
from .data import SamsungFrameData
from .exceptions import SamsungFrameApiClientError
from .services import async_register_services

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.device_registry import DeviceEntry
    from homeassistant.helpers.typing import ConfigType

    from .data import SamsungFrameConfigData, SamsungFrameConfigEntry

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(
    hass: HomeAssistant,
    config: ConfigType,  # noqa: ARG001 -- part of the signature Home Assistant calls
) -> bool:
    """Register the integration-level actions."""
    async_register_services(hass)
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SamsungFrameConfigEntry,
) -> bool:
    """Set up Samsung The Frame from a config entry."""
    config = cast("SamsungFrameConfigData", entry.data)
    client = SamsungFrameApiClient(hass, host=config["host"], token=config["token"])
    try:
        device_info = await client.async_get_device_info()
    except SamsungFrameApiClientError as exception:
        raise ConfigEntryNotReady(exception) from exception

    artwork_names = SamsungFrameArtworkNames(hass, entry.entry_id)
    await artwork_names.async_load()

    scan_interval_seconds: int = int(
        entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_SECONDS),
    )
    coordinator = SamsungFrameDataUpdateCoordinator(
        hass=hass,
        scan_interval=timedelta(seconds=scan_interval_seconds),
        config_entry=entry,
    )
    entry.runtime_data = SamsungFrameData(
        client=client,
        artwork_names=artwork_names,
        coordinator=coordinator,
        device_info=device_info,
        integration=async_get_loaded_integration(hass, entry.domain),
    )

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: SamsungFrameConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(
    hass: HomeAssistant,
    entry: SamsungFrameConfigEntry,
) -> None:
    """Delete the stored artwork names together with the entry."""
    await SamsungFrameArtworkNames(hass, entry.entry_id).async_delete_storage()


async def async_reload_entry(
    hass: HomeAssistant,
    entry: SamsungFrameConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_config_entry_device(
    hass: HomeAssistant,  # noqa: ARG001 -- part of the signature Home Assistant calls
    entry: SamsungFrameConfigEntry,
    device_entry: DeviceEntry,
) -> bool:
    """Allow deleting every device except the TV this entry was set up for."""
    return (DOMAIN, entry.runtime_data.device_info["device_id"]) not in (
        device_entry.identifiers
    )
