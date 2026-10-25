from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.helpers import device_registry as dr

from custom_components.samsung_frame import (
    async_reload_entry,
    async_remove_config_entry_device,
)
from custom_components.samsung_frame.const import (
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DOMAIN,
)
from custom_components.samsung_frame.exceptions import (
    SamsungFrameApiClientCommunicationError,
)

from .conftest import DEVICE_ID, HOST, TOKEN


async def test_setup_entry_loads_successfully(hass, setup_integration):
    assert setup_integration.state == ConfigEntryState.LOADED


async def test_setup_entry_builds_the_client_from_the_entry(hass, setup_integration):
    from custom_components import samsung_frame

    samsung_frame.SamsungFrameApiClient.assert_called_once_with(
        hass, host=HOST, token=TOKEN
    )


async def test_setup_entry_creates_entities(hass, setup_integration):
    assert len(hass.states.async_all("switch")) == 1
    assert len(hass.states.async_all("sensor")) == 1


async def test_setup_entry_registers_update_listener(hass, setup_integration):
    assert len(setup_integration.update_listeners) == 1


async def test_setup_entry_retries_when_device_info_fails(
    hass, mock_api_client, config_entry, enable_custom_integrations
):
    mock_api_client.async_get_device_info.side_effect = (
        SamsungFrameApiClientCommunicationError("down")
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state == ConfigEntryState.SETUP_RETRY


async def test_setup_entry_retries_when_first_refresh_fails(
    hass, mock_api_client, config_entry, enable_custom_integrations
):
    mock_api_client.async_get_art_state.side_effect = (
        SamsungFrameApiClientCommunicationError("down")
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state == ConfigEntryState.SETUP_RETRY


async def test_services_are_registered(hass, setup_integration):
    for service in ("upload_artwork", "select_artwork", "delete_artwork"):
        assert hass.services.has_service(DOMAIN, service)


async def test_unload_entry_succeeds(hass, setup_integration):
    assert await hass.config_entries.async_unload(setup_integration.entry_id)
    assert setup_integration.state == ConfigEntryState.NOT_LOADED


async def test_async_reload_entry_reloads(hass, setup_integration):
    await async_reload_entry(hass, setup_integration)
    await hass.async_block_till_done()
    assert setup_integration.state == ConfigEntryState.LOADED


async def test_runtime_data_populated(hass, setup_integration, device_info):
    runtime_data = setup_integration.runtime_data
    assert runtime_data.client is not None
    assert runtime_data.coordinator is not None
    assert runtime_data.integration is not None
    assert runtime_data.device_info == device_info


async def test_scan_interval_defaults_to_const(hass, setup_integration):
    assert setup_integration.runtime_data.coordinator.update_interval == timedelta(
        seconds=DEFAULT_SCAN_INTERVAL_SECONDS
    )


async def test_scan_interval_picks_up_options(
    hass, mock_api_client, config_entry, enable_custom_integrations
):
    config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        config_entry, options={CONF_SCAN_INTERVAL: 60}
    )
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.runtime_data.coordinator.update_interval == timedelta(
        seconds=60
    )


async def test_remove_device_refuses_the_tv(hass, setup_integration):
    device = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, DEVICE_ID), setup_integration.entry_id
    )
    assert device is not None
    assert not await async_remove_config_entry_device(hass, setup_integration, device)


async def test_remove_device_allows_a_stale_device(hass, setup_integration):
    stale = dr.async_get(hass).async_get_or_create(
        config_entry_id=setup_integration.entry_id,
        identifiers={(DOMAIN, "device-that-went-away")},
    )
    assert await async_remove_config_entry_device(hass, setup_integration, stale)
