from __future__ import annotations

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.samsung_frame.const import DOMAIN
from custom_components.samsung_frame.device_identity import (
    SamsungFrameDeviceIdentity,
)

from .conftest import DEVICE_ID, DEVICE_INFO

UPDATED_DEVICE_ID = "0880147b-37af-423b-bd8c-7f6388d89d92"


def _identity(hass, entry) -> SamsungFrameDeviceIdentity:
    return SamsungFrameDeviceIdentity(hass, entry)


async def test_same_id_is_the_same_tv(hass, config_entry):
    config_entry.add_to_hass(hass)
    assert _identity(hass, config_entry).is_same_tv(dict(DEVICE_INFO))


async def test_new_id_with_the_registered_mac_is_the_same_tv(hass, setup_integration):
    reported = {**DEVICE_INFO, "device_id": UPDATED_DEVICE_ID}
    assert _identity(hass, setup_integration).is_same_tv(reported)


async def test_new_id_with_another_mac_is_another_tv(hass, setup_integration):
    reported = {
        **DEVICE_INFO,
        "device_id": UPDATED_DEVICE_ID,
        "mac": "00:11:22:33:44:55",
    }
    assert not _identity(hass, setup_integration).is_same_tv(reported)


async def test_new_id_without_a_reported_mac_is_another_tv(hass, setup_integration):
    reported = {**DEVICE_INFO, "device_id": UPDATED_DEVICE_ID, "mac": None}
    assert not _identity(hass, setup_integration).is_same_tv(reported)


async def test_new_id_without_a_registered_device_is_another_tv(hass, config_entry):
    config_entry.add_to_hass(hass)
    reported = {**DEVICE_INFO, "device_id": UPDATED_DEVICE_ID}
    assert not _identity(hass, config_entry).is_same_tv(reported)


async def test_adopt_moves_the_entry_device_and_entities(
    hass, setup_integration, mock_api_client
):
    mock_api_client.async_get_device_info.return_value = {
        **DEVICE_INFO,
        "device_id": UPDATED_DEVICE_ID,
    }
    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)
    device = device_registry.async_get_device_by_identifier(
        (DOMAIN, DEVICE_ID), setup_integration.entry_id
    )
    entity_ids = {
        entity.entity_id
        for entity in er.async_entries_for_config_entry(
            entity_registry, setup_integration.entry_id
        )
    }

    _identity(hass, setup_integration).async_adopt(
        {**DEVICE_INFO, "device_id": UPDATED_DEVICE_ID}
    )

    assert setup_integration.unique_id == UPDATED_DEVICE_ID
    moved_device = device_registry.async_get(device.id)
    assert moved_device.identifiers == {(DOMAIN, UPDATED_DEVICE_ID)}
    moved_entities = er.async_entries_for_config_entry(
        entity_registry, setup_integration.entry_id
    )
    assert {entity.entity_id for entity in moved_entities} == entity_ids
    assert {entity.unique_id for entity in moved_entities} == {
        f"{UPDATED_DEVICE_ID}_art_mode",
        f"{UPDATED_DEVICE_ID}_current_artwork",
    }


async def test_adopt_keeps_entities_of_other_devices(
    hass, setup_integration, mock_api_client
):
    mock_api_client.async_get_device_info.return_value = {
        **DEVICE_INFO,
        "device_id": UPDATED_DEVICE_ID,
    }
    entity_registry = er.async_get(hass)
    stray = entity_registry.async_get_or_create(
        "sensor", DOMAIN, "stray", config_entry=setup_integration
    )

    _identity(hass, setup_integration).async_adopt(
        {**DEVICE_INFO, "device_id": UPDATED_DEVICE_ID}
    )

    assert entity_registry.async_get(stray.entity_id).unique_id == "stray"


async def test_adopt_with_the_same_id_changes_nothing(hass, setup_integration):
    _identity(hass, setup_integration).async_adopt(dict(DEVICE_INFO))
    assert setup_integration.unique_id == DEVICE_ID


async def test_adopt_without_a_registered_device_moves_the_entry(hass, config_entry):
    config_entry.add_to_hass(hass)
    _identity(hass, config_entry).async_adopt(
        {**DEVICE_INFO, "device_id": UPDATED_DEVICE_ID}
    )
    assert config_entry.unique_id == UPDATED_DEVICE_ID
