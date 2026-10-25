"""Communication error raised by the API client."""

from __future__ import annotations

from .api_client_error import SamsungFrameApiClientError


class SamsungFrameApiClientCommunicationError(SamsungFrameApiClientError):
    """Exception to indicate the TV could not be reached."""
