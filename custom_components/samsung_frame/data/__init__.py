"""Custom types for samsung_frame."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .art_state import SamsungFrameArtState
from .artwork_image import SamsungFrameArtworkImage
from .artwork_names_data import SamsungFrameArtworkNamesData
from .config_data import SamsungFrameConfigData
from .device_info import SamsungFrameDeviceInfo
from .diagnostics_entry import SamsungFrameDiagnosticsEntry
from .diagnostics_payload import SamsungFrameDiagnosticsPayload
from .host_input import SamsungFrameHostInput
from .options_data import SamsungFrameOptionsData
from .reframed_artwork import ReframedArtwork
from .reframed_artwork_page import ReframedArtworkPage
from .reframed_folder import ReframedFolder
from .reframed_tile import ReframedTile
from .runtime import SamsungFrameData

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry


type SamsungFrameConfigEntry = ConfigEntry[SamsungFrameData]

__all__ = [
    "ReframedArtwork",
    "ReframedArtworkPage",
    "ReframedFolder",
    "ReframedTile",
    "SamsungFrameArtState",
    "SamsungFrameArtworkImage",
    "SamsungFrameArtworkNamesData",
    "SamsungFrameConfigData",
    "SamsungFrameConfigEntry",
    "SamsungFrameData",
    "SamsungFrameDeviceInfo",
    "SamsungFrameDiagnosticsEntry",
    "SamsungFrameDiagnosticsPayload",
    "SamsungFrameHostInput",
    "SamsungFrameOptionsData",
]
