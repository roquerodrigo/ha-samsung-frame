from __future__ import annotations

import copy
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

pytest_plugins = "pytest_homeassistant_custom_component"

DEVICE_ID = "784b12b6-0e03-4fd9-9c41-92eefcba3657"
HOST = "192.168.1.50"
TOKEN = "12345678"

DEVICE_INFO = {
    "device_id": DEVICE_ID,
    "name": "Living Room TV",
    "model_name": "QN55LS03FAGXZD",
    "mac": "74:6d:fa:63:59:4d",
    "frame_tv_support": True,
}

ART_STATE = {"art_mode": True, "current_artwork_id": "MY_F0004"}


@pytest.fixture
def device_info() -> dict:
    return copy.deepcopy(DEVICE_INFO)


@pytest.fixture
def art_state() -> dict:
    return copy.deepcopy(ART_STATE)


@pytest.fixture
def mock_api_client(device_info: dict, art_state: dict) -> Generator:
    with patch("custom_components.samsung_frame.SamsungFrameApiClient") as mock_class:
        instance = mock_class.return_value
        instance.async_get_device_info = AsyncMock(return_value=device_info)
        instance.async_get_art_state = AsyncMock(return_value=art_state)
        instance.async_set_art_mode = AsyncMock(return_value=None)
        instance.async_upload_artwork = AsyncMock(return_value="MY_F0020")
        instance.async_select_artwork = AsyncMock(return_value=None)
        instance.async_delete_artwork = AsyncMock(return_value=None)
        yield instance


@pytest.fixture
def config_entry():
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.samsung_frame.const import DOMAIN

    return MockConfigEntry(
        domain=DOMAIN,
        title="Living Room TV",
        data={"host": HOST, "token": TOKEN},
        unique_id=DEVICE_ID,
    )


@pytest.fixture
async def setup_integration(
    hass, mock_api_client, config_entry, enable_custom_integrations
):
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry
