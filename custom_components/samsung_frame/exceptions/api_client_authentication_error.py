"""Authentication error raised by the API client."""

from __future__ import annotations

from .api_client_error import SamsungFrameApiClientError


class SamsungFrameApiClientAuthenticationError(SamsungFrameApiClientError):
    """Exception to indicate the TV refused the connection."""
