"""Constants for samsung_frame."""

from __future__ import annotations

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "samsung_frame"
MANUFACTURER = "Samsung"

# The TV grants access per client name; sharing the name used by the core
# Samsung TV integration reuses an authorization the user already accepted.
CLIENT_NAME = "HomeAssistant"
WEBSOCKET_PORT = 8002

REQUEST_TIMEOUT_SECONDS = 10
PAIRING_TIMEOUT_SECONDS = 30
UPLOAD_TIMEOUT_SECONDS = 60
DOWNLOAD_TIMEOUT_SECONDS = 30

DEFAULT_SCAN_INTERVAL_SECONDS = 30
MIN_SCAN_INTERVAL_SECONDS = 10

REFRAMED_NAME = "Reframed Gallery"
REFRAMED_BASE_URL = "https://www.reframed.gallery"
REFRAMED_USER_AGENT = (
    "HomeAssistant-SamsungFrame (+https://github.com/roquerodrigo/ha-samsung-frame)"
)
REFRAMED_REQUEST_TIMEOUT_SECONDS = 15
REFRAMED_PAGE_CACHE_SECONDS = 3600
