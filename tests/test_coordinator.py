from __future__ import annotations

import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.samsung_frame.exceptions import (
    SamsungFrameApiClientAuthenticationError,
    SamsungFrameApiClientCommunicationError,
)


async def test_update_returns_art_state(hass, setup_integration, art_state):
    coordinator = setup_integration.runtime_data.coordinator
    assert await coordinator._async_update_data() == art_state


async def test_authentication_error_starts_reauth(
    hass, setup_integration, mock_api_client
):
    mock_api_client.async_get_art_state.side_effect = (
        SamsungFrameApiClientAuthenticationError("refused")
    )
    with pytest.raises(ConfigEntryAuthFailed):
        await setup_integration.runtime_data.coordinator._async_update_data()


async def test_communication_error_raises_update_failed(
    hass, setup_integration, mock_api_client
):
    mock_api_client.async_get_art_state.side_effect = (
        SamsungFrameApiClientCommunicationError("down")
    )
    with pytest.raises(UpdateFailed):
        await setup_integration.runtime_data.coordinator._async_update_data()


async def test_failed_refresh_marks_entities_unavailable(
    hass, setup_integration, mock_api_client
):
    mock_api_client.async_get_art_state.side_effect = (
        SamsungFrameApiClientCommunicationError("down")
    )
    await setup_integration.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get("switch.living_room_tv_art_mode").state == "unavailable"
