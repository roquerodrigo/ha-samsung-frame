from __future__ import annotations

from homeassistant.helpers import device_registry as dr

from custom_components.samsung_frame.const import DOMAIN

from .conftest import DEVICE_ID


async def test_device_registered_with_tv_identity(hass, setup_integration):
    device = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, DEVICE_ID), setup_integration.entry_id
    )
    assert device is not None
    assert device.name == "Living Room TV"
    assert device.manufacturer == "Samsung"
    assert device.model == "QN55LS03FAGXZD"
    assert (dr.CONNECTION_NETWORK_MAC, "74:6d:fa:63:59:4d") in device.connections


async def test_device_without_mac_has_no_connections(
    hass, mock_api_client, device_info, config_entry, enable_custom_integrations
):
    device_info["mac"] = None
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    device = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, DEVICE_ID), config_entry.entry_id
    )
    assert device is not None
    assert device.connections == set()
