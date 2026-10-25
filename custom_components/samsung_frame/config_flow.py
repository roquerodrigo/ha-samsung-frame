"""Config flow for samsung_frame."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import probatio
from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.core import callback
from homeassistant.helpers import selector

from .api import SamsungFrameApiClient
from .const import DOMAIN, LOGGER
from .exceptions import (
    SamsungFrameApiClientAuthenticationError,
    SamsungFrameApiClientCommunicationError,
    SamsungFrameApiClientError,
)
from .options_flow import SamsungFrameOptionsFlow

if TYPE_CHECKING:
    from collections.abc import Mapping

    from .data import (
        SamsungFrameConfigData,
        SamsungFrameConfigEntry,
        SamsungFrameDeviceInfo,
        SamsungFrameHostInput,
    )


def _host_schema(default_host: str | None = None) -> probatio.Schema:
    """Build the host schema, optionally pre-filled."""
    return probatio.Schema(
        {
            probatio.Required(
                CONF_HOST,
                default=default_host
                if default_host is not None
                else probatio.UNDEFINED,
            ): selector.TextSelector(),
        },
    )


class SamsungFrameFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """
    Config flow for Samsung The Frame.

    Setup happens in two steps: the host is checked over REST first, then a
    connection is opened that the user has to approve on the TV screen, which
    is what hands out the token every later connection presents.
    """

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow state shared between the steps."""
        self._host: str | None = None
        self._device_name: str | None = None

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: SamsungFrameConfigEntry,  # noqa: ARG004
    ) -> SamsungFrameOptionsFlow:
        """Return the options flow handler."""
        return SamsungFrameOptionsFlow()

    # The narrowed ``SamsungFrameHostInput`` parameter is intentional — HA's
    # base class declares ``dict[str, Any] | None`` here, and we trade strict
    # LSP compliance for stronger typing of our own user_input schema.
    async def async_step_user(  # type: ignore[override]
        self,
        user_input: SamsungFrameHostInput | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Ask for the address of the TV."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            device_info, errors = await self._async_read_device_info(host)
            if device_info is not None:
                await self.async_set_unique_id(device_info["device_id"])
                self._abort_if_unique_id_configured(updates={CONF_HOST: host})
                self._host = host
                self._device_name = device_info["name"]
                return await self.async_step_pair()

        return self.async_show_form(
            step_id="user",
            data_schema=_host_schema(user_input[CONF_HOST] if user_input else None),
            errors=errors,
        )

    async def async_step_pair(
        self,
        user_input: Mapping[str, str] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Pair with the TV once the user is ready to approve the request."""
        errors: dict[str, str] = {}
        host = cast("str", self._host)
        device_name = cast("str", self._device_name)

        if user_input is not None:
            token, errors = await self._async_pair(host)
            if not errors:
                data: SamsungFrameConfigData = {"host": host, "token": token}
                return self.async_create_entry(title=device_name, data=dict(data))

        return self.async_show_form(
            step_id="pair",
            description_placeholders={"name": device_name},
            errors=errors,
        )

    async def async_step_reauth(
        self,
        entry_data: Mapping[str, str],  # noqa: ARG002
    ) -> config_entries.ConfigFlowResult:
        """Pair again when the TV stops accepting the stored token."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self,
        user_input: Mapping[str, str] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Ask the user to approve a new pairing request on the TV."""
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        existing = cast("SamsungFrameConfigData", entry.data)

        if user_input is not None:
            token, errors = await self._async_pair(existing["host"])
            if not errors:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={"token": token},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            description_placeholders={"name": entry.title},
            errors=errors,
        )

    async def async_step_reconfigure(
        self,
        user_input: SamsungFrameHostInput | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Point an existing entry at the new address of the same TV."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()
        existing = cast("SamsungFrameConfigData", entry.data)

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            device_info, errors = await self._async_read_device_info(host)
            if device_info is not None:
                await self.async_set_unique_id(device_info["device_id"])
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={CONF_HOST: host},
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_host_schema(existing["host"]),
            errors=errors,
        )

    async def _async_read_device_info(
        self,
        host: str,
    ) -> tuple[SamsungFrameDeviceInfo | None, dict[str, str]]:
        """Return the device information, or the form errors explaining why not."""
        client = SamsungFrameApiClient(self.hass, host=host, token=None)
        try:
            device_info = await client.async_get_device_info()
        except SamsungFrameApiClientCommunicationError as exception:
            LOGGER.warning("Failed to reach the TV: %s", exception)
            return None, {"base": "cannot_connect"}
        except SamsungFrameApiClientError:
            LOGGER.exception("Failed to read the device information")
            return None, {"base": "unknown"}
        if not device_info["frame_tv_support"]:
            return None, {"base": "not_supported"}
        return device_info, {}

    async def _async_pair(self, host: str) -> tuple[str | None, dict[str, str]]:
        """Return the token the TV issued, or the form errors explaining why not."""
        client = SamsungFrameApiClient(self.hass, host=host, token=None)
        try:
            return await client.async_pair(), {}
        except SamsungFrameApiClientAuthenticationError as exception:
            LOGGER.warning("The TV refused the pairing request: %s", exception)
            return None, {"base": "pairing_refused"}
        except SamsungFrameApiClientCommunicationError as exception:
            LOGGER.warning("Failed to pair with the TV: %s", exception)
            return None, {"base": "pairing_timeout"}
        except SamsungFrameApiClientError:
            LOGGER.exception("Failed to pair with the TV")
            return None, {"base": "unknown"}
