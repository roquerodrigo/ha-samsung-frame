"""Typed shape of the host form submitted in the config flow."""

from __future__ import annotations

from typing import TypedDict


class SamsungFrameHostInput(TypedDict):
    """Shape of the host form submitted in the config flow."""

    host: str
