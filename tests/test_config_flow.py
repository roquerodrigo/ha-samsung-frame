from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.samsung_frame.const import DOMAIN
from custom_components.samsung_frame.exceptions import (
    SamsungFrameApiClientAuthenticationError,
    SamsungFrameApiClientCommunicationError,
    SamsungFrameApiClientError,
)

from .conftest import DEVICE_ID, DEVICE_INFO, HOST, TOKEN

NEW_HOST = "192.168.1.60"


@pytest.fixture
def flow_client():
    with patch(
        "custom_components.samsung_frame.config_flow.SamsungFrameApiClient"
    ) as client_class:
        instance = client_class.return_value
        instance.async_get_device_info = AsyncMock(return_value=dict(DEVICE_INFO))
        instance.async_pair = AsyncMock(return_value=TOKEN)
        instance.client_class = client_class
        yield instance


@pytest.fixture(autouse=True)
def skip_setup():
    with patch(
        "custom_components.samsung_frame.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


async def _start_user_flow(hass):
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )


async def _submit_host(hass, host=HOST):
    flow = await _start_user_flow(hass)
    return await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={"host": host}
    )


async def test_step_user_shows_form(hass, enable_custom_integrations):
    result = await _start_user_flow(hass)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_valid_host_moves_to_pairing(
    hass, enable_custom_integrations, flow_client
):
    result = await _submit_host(hass, host=f"  {HOST} ")
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "pair"
    assert result["description_placeholders"] == {"name": "Living Room TV"}
    assert flow_client.client_class.call_args.kwargs == {"host": HOST, "token": None}


async def test_pairing_creates_entry(hass, enable_custom_integrations, flow_client):
    result = await _submit_host(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Living Room TV"
    assert result["data"] == {"host": HOST, "token": TOKEN}
    assert result["result"].unique_id == DEVICE_ID


@pytest.mark.parametrize(
    ("side_effect", "error"),
    [
        (SamsungFrameApiClientAuthenticationError("refused"), "pairing_refused"),
        (SamsungFrameApiClientCommunicationError("timeout"), "pairing_timeout"),
        (SamsungFrameApiClientError("odd"), "unknown"),
    ],
)
async def test_pairing_errors_keep_the_form(
    hass, enable_custom_integrations, flow_client, side_effect, error
):
    flow_client.async_pair.side_effect = side_effect
    result = await _submit_host(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "pair"
    assert result["errors"] == {"base": error}


async def test_pairing_can_be_retried(hass, enable_custom_integrations, flow_client):
    flow_client.async_pair.side_effect = [
        SamsungFrameApiClientCommunicationError("timeout"),
        TOKEN,
    ]
    result = await _submit_host(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY


@pytest.mark.parametrize(
    ("side_effect", "error"),
    [
        (SamsungFrameApiClientCommunicationError("down"), "cannot_connect"),
        (SamsungFrameApiClientError("odd"), "unknown"),
    ],
)
async def test_host_errors_keep_the_form(
    hass, enable_custom_integrations, flow_client, side_effect, error
):
    flow_client.async_get_device_info.side_effect = side_effect
    result = await _submit_host(hass)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": error}


async def test_tv_without_art_mode_is_rejected(
    hass, enable_custom_integrations, flow_client
):
    flow_client.async_get_device_info.return_value = {
        **DEVICE_INFO,
        "frame_tv_support": False,
    }
    result = await _submit_host(hass)
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "not_supported"}


async def test_configured_tv_aborts_and_updates_host(
    hass, enable_custom_integrations, flow_client, config_entry
):
    config_entry.add_to_hass(hass)
    result = await _submit_host(hass, host=NEW_HOST)
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert config_entry.data["host"] == NEW_HOST


async def test_reauth_shows_confirm_form(
    hass, enable_custom_integrations, config_entry
):
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["description_placeholders"] == {"name": "Living Room TV"}


async def test_reauth_stores_the_new_token(
    hass, enable_custom_integrations, flow_client, config_entry
):
    config_entry.add_to_hass(hass)
    flow_client.async_pair.return_value = "new-token"
    result = await config_entry.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert config_entry.data == {"host": HOST, "token": "new-token"}


async def test_reauth_refused_shows_error(
    hass, enable_custom_integrations, flow_client, config_entry
):
    config_entry.add_to_hass(hass)
    flow_client.async_pair.side_effect = SamsungFrameApiClientAuthenticationError(
        "refused"
    )
    result = await config_entry.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "pairing_refused"}
    assert config_entry.data["token"] == TOKEN


async def test_reconfigure_shows_form(hass, enable_custom_integrations, config_entry):
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reconfigure"


async def test_reconfigure_updates_host_and_keeps_token(
    hass, enable_custom_integrations, flow_client, config_entry
):
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"host": NEW_HOST}
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert config_entry.data == {"host": NEW_HOST, "token": TOKEN}


async def test_reconfigure_to_another_tv_aborts(
    hass, enable_custom_integrations, flow_client, config_entry
):
    config_entry.add_to_hass(hass)
    flow_client.async_get_device_info.return_value = {
        **DEVICE_INFO,
        "device_id": "another-tv",
    }
    result = await config_entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"host": NEW_HOST}
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "unique_id_mismatch"
    assert config_entry.data["host"] == HOST


async def test_reconfigure_unreachable_shows_error(
    hass, enable_custom_integrations, flow_client, config_entry
):
    config_entry.add_to_hass(hass)
    flow_client.async_get_device_info.side_effect = (
        SamsungFrameApiClientCommunicationError("down")
    )
    result = await config_entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"host": NEW_HOST}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
