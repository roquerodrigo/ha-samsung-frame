"""Integration-level actions for samsung_frame."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.core import SupportsResponse

from ..const import DOMAIN
from .const import (
    SERVICE_DELETE_ARTWORK,
    SERVICE_RENAME_ARTWORK,
    SERVICE_SELECT_ARTWORK,
    SERVICE_UPLOAD_ARTWORK,
)
from .delete_artwork import DELETE_ARTWORK_SCHEMA, SamsungFrameDeleteArtworkService
from .rename_artwork import RENAME_ARTWORK_SCHEMA, SamsungFrameRenameArtworkService
from .select_artwork import SELECT_ARTWORK_SCHEMA, SamsungFrameSelectArtworkService
from .upload_artwork import UPLOAD_ARTWORK_SCHEMA, SamsungFrameUploadArtworkService

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


def async_register_services(hass: HomeAssistant) -> None:
    """Register the integration-level actions."""
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPLOAD_ARTWORK,
        SamsungFrameUploadArtworkService(hass).async_handle,
        schema=UPLOAD_ARTWORK_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SELECT_ARTWORK,
        SamsungFrameSelectArtworkService(hass).async_handle,
        schema=SELECT_ARTWORK_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_ARTWORK,
        SamsungFrameDeleteArtworkService(hass).async_handle,
        schema=DELETE_ARTWORK_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RENAME_ARTWORK,
        SamsungFrameRenameArtworkService(hass).async_handle,
        schema=RENAME_ARTWORK_SCHEMA,
    )
