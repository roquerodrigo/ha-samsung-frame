"""Typed top-level shape returned by async_get_config_entry_diagnostics."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from collections.abc import Mapping

    from .art_state import SamsungFrameArtState
    from .diagnostics_entry import SamsungFrameDiagnosticsEntry


class SamsungFrameDiagnosticsPayload(TypedDict):
    """Top-level shape returned by async_get_config_entry_diagnostics."""

    entry: SamsungFrameDiagnosticsEntry
    device: Mapping[str, str | bool | None]
    coordinator_data: SamsungFrameArtState | None
