"""Typed shape of the connection settings persisted on the config entry."""

from __future__ import annotations

from typing import TypedDict


class SamsungFrameConfigData(TypedDict):
    """Shape of the connection settings persisted on the config entry."""

    host: str
    token: str | None
