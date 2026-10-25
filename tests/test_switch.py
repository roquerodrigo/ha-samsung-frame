from __future__ import annotations

import pytest
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from custom_components.samsung_frame.exceptions import (
    SamsungFrameApiClientCommunicationError,
)

from .conftest import DEVICE_ID

ENTITY_ID = "switch.living_room_tv_art_mode"


async def test_switch_reports_art_mode(hass, setup_integration):
    assert hass.states.get(ENTITY_ID).state == "on"


async def test_switch_unique_id(hass, setup_integration):
    entry = er.async_get(hass).async_get(ENTITY_ID)
    assert entry.unique_id == f"{DEVICE_ID}_art_mode"


async def test_turn_off_leaves_art_mode(hass, setup_integration, mock_api_client):
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": ENTITY_ID}, blocking=True
    )
    mock_api_client.async_set_art_mode.assert_awaited_once_with(enabled=False)
    assert hass.states.get(ENTITY_ID).state == "off"
    assert hass.states.get("sensor.living_room_tv_current_artwork").state == "MY_F0004"


async def test_turn_on_enters_art_mode(hass, setup_integration, mock_api_client):
    setup_integration.runtime_data.coordinator.async_set_updated_data(
        {"art_mode": False, "current_artwork_id": "MY_F0004"}
    )
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": ENTITY_ID}, blocking=True
    )
    mock_api_client.async_set_art_mode.assert_awaited_once_with(enabled=True)
    assert hass.states.get(ENTITY_ID).state == "on"


async def test_failed_toggle_raises_translated_error(
    hass, setup_integration, mock_api_client
):
    mock_api_client.async_set_art_mode.side_effect = (
        SamsungFrameApiClientCommunicationError("down")
    )
    with pytest.raises(HomeAssistantError) as error:
        await hass.services.async_call(
            "switch", "turn_off", {"entity_id": ENTITY_ID}, blocking=True
        )
    assert error.value.translation_key == "art_mode_failed"
    assert hass.states.get(ENTITY_ID).state == "on"


async def test_switch_state_none_before_first_refresh(hass, setup_integration):
    from custom_components.samsung_frame.switch import SamsungFrameArtModeSwitch

    coordinator = setup_integration.runtime_data.coordinator
    coordinator.data = None
    assert SamsungFrameArtModeSwitch(coordinator).is_on is None


async def test_toggle_before_first_refresh_keeps_artwork_unknown(
    hass, setup_integration, mock_api_client
):
    from custom_components.samsung_frame.switch import SamsungFrameArtModeSwitch

    coordinator = setup_integration.runtime_data.coordinator
    coordinator.data = None
    switch = SamsungFrameArtModeSwitch(coordinator)
    await switch.async_turn_on()
    assert coordinator.data == {"art_mode": True, "current_artwork_id": None}
