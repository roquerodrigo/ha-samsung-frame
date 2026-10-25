from __future__ import annotations

from homeassistant.helpers import entity_registry as er

from .conftest import DEVICE_ID

ENTITY_ID = "sensor.living_room_tv_current_artwork"


async def test_sensor_reports_current_artwork(hass, setup_integration):
    assert hass.states.get(ENTITY_ID).state == "MY_F0004"


async def test_sensor_unique_id(hass, setup_integration):
    entry = er.async_get(hass).async_get(ENTITY_ID)
    assert entry.unique_id == f"{DEVICE_ID}_current_artwork"


async def test_sensor_unknown_without_artwork(hass, setup_integration):
    coordinator = setup_integration.runtime_data.coordinator
    coordinator.async_set_updated_data({"art_mode": False, "current_artwork_id": None})
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == "unknown"


async def test_sensor_value_none_before_first_refresh(hass, setup_integration):
    from custom_components.samsung_frame.sensor import (
        SamsungFrameCurrentArtworkSensor,
    )

    coordinator = setup_integration.runtime_data.coordinator
    coordinator.data = None
    assert SamsungFrameCurrentArtworkSensor(coordinator).native_value is None
