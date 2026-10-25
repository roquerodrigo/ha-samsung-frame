from __future__ import annotations

from custom_components.samsung_frame.diagnostics import (
    async_get_config_entry_diagnostics,
)

from .conftest import HOST


async def test_diagnostics_redacts_token(hass, setup_integration):
    diagnostics = await async_get_config_entry_diagnostics(hass, setup_integration)
    assert diagnostics["entry"]["data"]["token"] == "**REDACTED**"
    assert diagnostics["entry"]["data"]["host"] == HOST


async def test_diagnostics_redacts_mac(hass, setup_integration):
    diagnostics = await async_get_config_entry_diagnostics(hass, setup_integration)
    assert diagnostics["device"]["mac"] == "**REDACTED**"
    assert diagnostics["device"]["model_name"] == "QN55LS03FAGXZD"


async def test_diagnostics_includes_entry_metadata(hass, setup_integration):
    diagnostics = await async_get_config_entry_diagnostics(hass, setup_integration)
    assert diagnostics["entry"]["domain"] == "samsung_frame"
    assert diagnostics["entry"]["version"] == 1
    assert diagnostics["entry"]["title"] == "Living Room TV"
    assert diagnostics["entry"]["options"] == {}


async def test_diagnostics_includes_coordinator_data(
    hass, setup_integration, art_state
):
    diagnostics = await async_get_config_entry_diagnostics(hass, setup_integration)
    assert diagnostics["coordinator_data"] == art_state
