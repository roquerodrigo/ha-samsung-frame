"""Client for the Art Mode API of Samsung The Frame televisions."""

from __future__ import annotations

import asyncio
import re
from contextlib import contextmanager
from typing import TYPE_CHECKING

import requests
from samsungtvws import SamsungTVArt
from samsungtvws import exceptions as samsung_exceptions
from samsungtvws.rest import SamsungTVRest
from websocket import WebSocketException

from .const import (
    CLIENT_NAME,
    PAIRING_TIMEOUT_SECONDS,
    REQUEST_TIMEOUT_SECONDS,
    UPLOAD_TIMEOUT_SECONDS,
    WEBSOCKET_PORT,
)
from .exceptions import (
    SamsungFrameApiClientAuthenticationError,
    SamsungFrameApiClientCommunicationError,
    SamsungFrameApiClientError,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from homeassistant.core import HomeAssistant

    from .data import (
        SamsungFrameArtState,
        SamsungFrameArtworkImage,
        SamsungFrameDeviceInfo,
    )

_TOKEN_QUERY = re.compile(r"token=[^&\s'\"]+")

_COMMUNICATION_ERRORS: tuple[type[Exception], ...] = (
    samsung_exceptions.ConnectionFailure,
    samsung_exceptions.HttpApiError,
    requests.RequestException,
    WebSocketException,
    OSError,
)
_RESPONSE_ERRORS: tuple[type[Exception], ...] = (
    samsung_exceptions.ResponseError,
    samsung_exceptions.MessageError,
    KeyError,
    TypeError,
    ValueError,
)


def _sanitized_error_text(exception: BaseException) -> str:
    """Strip the pairing token from upstream error text before it reaches the log."""
    return _TOKEN_QUERY.sub("token=<redacted>", str(exception))


@contextmanager
def _translated_errors(action: str) -> Iterator[None]:
    """Map the upstream library exceptions onto the integration hierarchy."""
    try:
        yield
    except samsung_exceptions.UnauthorizedError as exception:
        msg = f"Failed to {action}: the TV refused the connection"
        raise SamsungFrameApiClientAuthenticationError(msg) from exception
    except _COMMUNICATION_ERRORS as exception:
        msg = f"Failed to {action}: {_sanitized_error_text(exception)}"
        raise SamsungFrameApiClientCommunicationError(msg) from exception
    except _RESPONSE_ERRORS as exception:
        msg = f"Failed to {action}: {_sanitized_error_text(exception)}"
        raise SamsungFrameApiClientError(msg) from exception


class SamsungFrameApiClient:
    """
    Talk to the Art Mode channel of a Samsung The Frame TV.

    The upstream library is synchronous, so every operation runs in the
    executor. Each operation opens its own connection and the lock keeps them
    from overlapping, because the TV handles concurrent art sessions poorly.
    """

    def __init__(self, hass: HomeAssistant, host: str, token: str | None) -> None:
        """Initialize the client for the TV at ``host``."""
        self._hass = hass
        self._host = host
        self._token = token
        self._lock = asyncio.Lock()

    async def async_get_device_info(self) -> SamsungFrameDeviceInfo:
        """Read the identity and capabilities the TV reports over REST."""
        async with self._lock:
            return await self._hass.async_add_executor_job(self._get_device_info)

    async def async_pair(self) -> str | None:
        """Open a connection the user approves on the TV and return its token."""
        async with self._lock:
            token = await self._hass.async_add_executor_job(self._pair)
        self._token = token
        return token

    async def async_get_art_state(self) -> SamsungFrameArtState:
        """Read the art mode status and the selected artwork."""
        async with self._lock:
            return await self._hass.async_add_executor_job(self._get_art_state)

    async def async_set_art_mode(self, *, enabled: bool) -> None:
        """Turn art mode on or off."""
        async with self._lock:
            await self._hass.async_add_executor_job(self._set_art_mode, enabled)

    async def async_upload_artwork(
        self,
        image: SamsungFrameArtworkImage,
        matte: str,
        *,
        show: bool,
    ) -> str:
        """Upload an image to the art collection and return its content id."""
        async with self._lock:
            return await self._hass.async_add_executor_job(
                self._upload_artwork, image, matte, show
            )

    async def async_select_artwork(self, content_id: str, *, show: bool) -> None:
        """Select an artwork from the collection."""
        async with self._lock:
            await self._hass.async_add_executor_job(
                self._select_artwork, content_id, show
            )

    async def async_delete_artwork(self, content_id: str) -> None:
        """Delete an artwork from the collection."""
        async with self._lock:
            await self._hass.async_add_executor_job(self._delete_artwork, content_id)

    def _get_device_info(self) -> SamsungFrameDeviceInfo:
        with _translated_errors("read the device information"):
            rest = SamsungTVRest(self._host, WEBSOCKET_PORT, REQUEST_TIMEOUT_SECONDS)
            device = rest.rest_device_info()["device"]
            mac = device.get("wifiMac")
            return {
                "device_id": str(device["id"]).removeprefix("uuid:"),
                "name": str(device["name"]),
                "model_name": str(device["modelName"]),
                "mac": str(mac) if mac else None,
                "frame_tv_support": str(device.get("FrameTVSupport")).lower() == "true",
            }

    def _pair(self) -> str | None:
        with self._art_connection(
            "pair with the TV", pairing=True, timeout=PAIRING_TIMEOUT_SECONDS
        ) as art:
            return art.token

    def _get_art_state(self) -> SamsungFrameArtState:
        with self._art_connection("read the art mode state") as art:
            art_mode = art.get_artmode()
            current_artwork = art.get_current()
        content_id = current_artwork.get("content_id")
        return {
            "art_mode": art_mode == "on",
            "current_artwork_id": str(content_id) if content_id else None,
        }

    def _set_art_mode(self, enabled: bool) -> None:  # noqa: FBT001 -- positional for the executor
        with self._art_connection("change the art mode") as art:
            art.set_artmode(enabled)

    def _upload_artwork(
        self,
        image: SamsungFrameArtworkImage,
        matte: str,
        show: bool,  # noqa: FBT001 -- positional for the executor
    ) -> str:
        with self._art_connection(
            "upload the artwork", timeout=UPLOAD_TIMEOUT_SECONDS
        ) as art:
            content_id = str(
                art.upload(
                    image.content,
                    matte=matte,
                    portrait_matte=matte,
                    file_type=image.file_type,
                )
            )
            if show:
                art.select_image(content_id, show=True)
        return content_id

    def _select_artwork(self, content_id: str, show: bool) -> None:  # noqa: FBT001 -- positional for the executor
        with self._art_connection("select the artwork") as art:
            art.select_image(content_id, show=show)

    def _delete_artwork(self, content_id: str) -> None:
        with self._art_connection("delete the artwork") as art:
            deleted = art.delete(content_id)
        if not deleted:
            msg = f"Failed to delete the artwork: the TV kept {content_id}"
            raise SamsungFrameApiClientError(msg)

    @contextmanager
    def _art_connection(
        self,
        action: str,
        *,
        pairing: bool = False,
        timeout: float = REQUEST_TIMEOUT_SECONDS,
    ) -> Iterator[SamsungTVArt]:
        art = SamsungTVArt(
            self._host,
            token=None if pairing else self._token,
            port=WEBSOCKET_PORT,
            timeout=timeout,
            key_press_delay=0,
            name=CLIENT_NAME,
        )
        with _translated_errors(action):
            try:
                art.open()
                yield art
            finally:
                art.close()
