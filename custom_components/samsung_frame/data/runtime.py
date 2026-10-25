"""Runtime data stored on entry.runtime_data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.loader import Integration

    from ..api import SamsungFrameApiClient
    from ..artwork_names import SamsungFrameArtworkNames
    from ..coordinator import SamsungFrameDataUpdateCoordinator
    from .device_info import SamsungFrameDeviceInfo


@dataclass
class SamsungFrameData:
    """Data stored on entry.runtime_data for a Samsung The Frame TV."""

    client: SamsungFrameApiClient
    artwork_names: SamsungFrameArtworkNames
    coordinator: SamsungFrameDataUpdateCoordinator
    device_info: SamsungFrameDeviceInfo
    integration: Integration
