from __future__ import annotations

from unittest.mock import patch

import pytest
import requests
from samsungtvws import exceptions as samsung_exceptions
from websocket import WebSocketTimeoutException

from custom_components.samsung_frame.api import (
    SamsungFrameApiClient,
    _sanitized_error_text,
)
from custom_components.samsung_frame.const import (
    CLIENT_NAME,
    PAIRING_TIMEOUT_SECONDS,
    REQUEST_TIMEOUT_SECONDS,
    UPLOAD_TIMEOUT_SECONDS,
    WEBSOCKET_PORT,
)
from custom_components.samsung_frame.data import SamsungFrameArtworkImage
from custom_components.samsung_frame.exceptions import (
    SamsungFrameApiClientAuthenticationError,
    SamsungFrameApiClientCommunicationError,
    SamsungFrameApiClientError,
)

HOST = "192.168.1.50"
TOKEN = "12345678"

REST_DEVICE_INFO = {
    "device": {
        "FrameTVSupport": "true",
        "id": "uuid:784b12b6-0e03-4fd9-9c41-92eefcba3657",
        "modelName": "QN55LS03FAGXZD",
        "name": "Living Room TV",
        "wifiMac": "74:6d:fa:63:59:4d",
    }
}


@pytest.fixture
def art():
    with patch("custom_components.samsung_frame.api.SamsungTVArt") as art_class:
        instance = art_class.return_value
        instance.token = TOKEN
        instance.get_artmode.return_value = "on"
        instance.get_current.return_value = {"content_id": "MY_F0004"}
        instance.upload.return_value = "MY_F0020"
        instance.delete.return_value = True
        instance.art_class = art_class
        yield instance


@pytest.fixture
def rest():
    with patch("custom_components.samsung_frame.api.SamsungTVRest") as rest_class:
        instance = rest_class.return_value
        instance.rest_device_info.return_value = REST_DEVICE_INFO
        instance.rest_class = rest_class
        yield instance


def _client(hass, token=TOKEN) -> SamsungFrameApiClient:
    return SamsungFrameApiClient(hass, host=HOST, token=token)


async def test_get_device_info_maps_rest_payload(hass, rest):
    device_info = await _client(hass).async_get_device_info()
    assert device_info == {
        "device_id": "784b12b6-0e03-4fd9-9c41-92eefcba3657",
        "name": "Living Room TV",
        "model_name": "QN55LS03FAGXZD",
        "mac": "74:6d:fa:63:59:4d",
        "frame_tv_support": True,
    }
    rest.rest_class.assert_called_once_with(
        HOST, WEBSOCKET_PORT, REQUEST_TIMEOUT_SECONDS
    )


async def test_get_device_info_reports_missing_frame_support(hass, rest):
    rest.rest_device_info.return_value = {
        "device": {
            "id": "uuid:abc",
            "modelName": "QN65Q60",
            "name": "Bedroom TV",
        }
    }
    device_info = await _client(hass).async_get_device_info()
    assert device_info["frame_tv_support"] is False
    assert device_info["mac"] is None


async def test_get_device_info_unreachable_is_communication_error(hass, rest):
    rest.rest_device_info.side_effect = samsung_exceptions.HttpApiError("down")
    with pytest.raises(SamsungFrameApiClientCommunicationError):
        await _client(hass).async_get_device_info()


async def test_get_device_info_read_timeout_is_communication_error(hass, rest):
    rest.rest_device_info.side_effect = requests.ReadTimeout("slow")
    with pytest.raises(SamsungFrameApiClientCommunicationError):
        await _client(hass).async_get_device_info()


async def test_get_device_info_unexpected_payload_is_api_error(hass, rest):
    rest.rest_device_info.return_value = {}
    with pytest.raises(SamsungFrameApiClientError) as error:
        await _client(hass).async_get_device_info()
    assert not isinstance(error.value, SamsungFrameApiClientCommunicationError)


async def test_art_connection_uses_stored_token(hass, art):
    await _client(hass).async_get_art_state()
    art.art_class.assert_called_once_with(
        HOST,
        token=TOKEN,
        port=WEBSOCKET_PORT,
        timeout=REQUEST_TIMEOUT_SECONDS,
        key_press_delay=0,
        name=CLIENT_NAME,
    )
    art.open.assert_called_once()
    art.close.assert_called_once()


async def test_get_art_state(hass, art):
    assert await _client(hass).async_get_art_state() == {
        "art_mode": True,
        "current_artwork_id": "MY_F0004",
    }


async def test_get_art_state_without_current_artwork(hass, art):
    art.get_artmode.return_value = "off"
    art.get_current.return_value = {}
    assert await _client(hass).async_get_art_state() == {
        "art_mode": False,
        "current_artwork_id": None,
    }


async def test_pair_connects_without_token_and_keeps_the_new_one(hass, art):
    art.token = "fresh-token"
    client = _client(hass, token=None)
    assert await client.async_pair() == "fresh-token"
    assert art.art_class.call_args.kwargs["token"] is None
    assert art.art_class.call_args.kwargs["timeout"] == PAIRING_TIMEOUT_SECONDS

    await client.async_get_art_state()
    assert art.art_class.call_args.kwargs["token"] == "fresh-token"


async def test_refused_connection_is_authentication_error(hass, art):
    art.open.side_effect = samsung_exceptions.UnauthorizedError({"event": "x"})
    with pytest.raises(SamsungFrameApiClientAuthenticationError):
        await _client(hass).async_get_art_state()
    art.close.assert_called_once()


async def test_timeout_is_communication_error(hass, art):
    art.open.side_effect = WebSocketTimeoutException("timed out")
    with pytest.raises(SamsungFrameApiClientCommunicationError):
        await _client(hass).async_pair()


async def test_unreachable_tv_is_communication_error(hass, art):
    art.open.side_effect = ConnectionRefusedError("refused")
    with pytest.raises(SamsungFrameApiClientCommunicationError):
        await _client(hass).async_get_art_state()


async def test_rejected_request_is_api_error(hass, art):
    art.set_artmode.side_effect = samsung_exceptions.ResponseError("error -1")
    with pytest.raises(SamsungFrameApiClientError):
        await _client(hass).async_set_art_mode(enabled=True)
    art.close.assert_called_once()


async def test_set_art_mode(hass, art):
    await _client(hass).async_set_art_mode(enabled=False)
    assert art.set_artmode.call_args.args == (False,)


async def test_upload_artwork_and_show_it(hass, art):
    image = SamsungFrameArtworkImage(content=b"\xff\xd8\xffdata", file_type="jpg")
    content_id = await _client(hass).async_upload_artwork(
        image, "shadowbox_polar", show=True
    )
    assert content_id == "MY_F0020"
    art.upload.assert_called_once_with(
        b"\xff\xd8\xffdata",
        matte="shadowbox_polar",
        portrait_matte="shadowbox_polar",
        file_type="jpg",
    )
    art.select_image.assert_called_once_with("MY_F0020", show=True)
    assert art.art_class.call_args.kwargs["timeout"] == UPLOAD_TIMEOUT_SECONDS


async def test_upload_artwork_without_showing_it(hass, art):
    image = SamsungFrameArtworkImage(content=b"png", file_type="png")
    await _client(hass).async_upload_artwork(image, "none", show=False)
    art.select_image.assert_not_called()


async def test_select_artwork(hass, art):
    await _client(hass).async_select_artwork("MY_F0004", show=False)
    art.select_image.assert_called_once_with("MY_F0004", show=False)


async def test_delete_artwork(hass, art):
    await _client(hass).async_delete_artwork("MY_F0004")
    art.delete.assert_called_once_with("MY_F0004")


async def test_delete_artwork_kept_by_tv_is_api_error(hass, art):
    art.delete.return_value = False
    with pytest.raises(SamsungFrameApiClientError):
        await _client(hass).async_delete_artwork("MY_F0004")


def test_sanitized_error_text_hides_token():
    error = OSError("wss://tv:8002/api/v2/channels/x?name=SA&token=12345678 failed")
    assert "12345678" not in _sanitized_error_text(error)
    assert "token=<redacted>" in _sanitized_error_text(error)


async def test_error_message_does_not_leak_token(hass, art):
    art.open.side_effect = OSError("wss://tv?token=12345678 unreachable")
    with pytest.raises(SamsungFrameApiClientCommunicationError) as error:
        await _client(hass).async_get_art_state()
    assert "12345678" not in str(error.value)


def test_exception_hierarchy():
    assert issubclass(
        SamsungFrameApiClientCommunicationError, SamsungFrameApiClientError
    )
    assert issubclass(
        SamsungFrameApiClientAuthenticationError, SamsungFrameApiClientError
    )
