"""Typed shape of the device information the TV reports over REST."""

from __future__ import annotations

from typing import TypedDict


class SamsungFrameDeviceInfo(TypedDict):
    """Identity and capabilities of the TV."""

    device_id: str
    name: str
    model_name: str
    mac: str | None
    frame_tv_support: bool
