"""Diagnostics support for samsung_frame."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from homeassistant.components.diagnostics import async_redact_data

if TYPE_CHECKING:
    from collections.abc import Mapping

    from homeassistant.core import HomeAssistant

    from .data import (
        SamsungFrameConfigEntry,
        SamsungFrameDiagnosticsEntry,
        SamsungFrameDiagnosticsPayload,
    )

TO_REDACT: frozenset[str] = frozenset({"token", "mac"})


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,  # noqa: ARG001
    entry: SamsungFrameConfigEntry,
) -> SamsungFrameDiagnosticsPayload:
    """Return diagnostics for a config entry."""
    redacted_data = cast(
        "Mapping[str, str | None]",
        async_redact_data(dict(entry.data), set(TO_REDACT)),
    )
    redacted_options = cast(
        "Mapping[str, str | int]",
        async_redact_data(dict(entry.options), set(TO_REDACT)),
    )
    redacted_device = cast(
        "Mapping[str, str | bool | None]",
        async_redact_data(dict(entry.runtime_data.device_info), set(TO_REDACT)),
    )
    diagnostics_entry: SamsungFrameDiagnosticsEntry = {
        "title": entry.title,
        "version": entry.version,
        "domain": entry.domain,
        "data": redacted_data,
        "options": redacted_options,
    }
    return {
        "entry": diagnostics_entry,
        "device": redacted_device,
        "coordinator_data": entry.runtime_data.coordinator.data,
    }
