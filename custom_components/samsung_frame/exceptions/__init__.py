"""Exception classes for the samsung_frame API client."""

from __future__ import annotations

from .api_client_authentication_error import SamsungFrameApiClientAuthenticationError
from .api_client_communication_error import SamsungFrameApiClientCommunicationError
from .api_client_error import SamsungFrameApiClientError
from .reframed_gallery_error import ReframedGalleryError

__all__ = [
    "ReframedGalleryError",
    "SamsungFrameApiClientAuthenticationError",
    "SamsungFrameApiClientCommunicationError",
    "SamsungFrameApiClientError",
]
