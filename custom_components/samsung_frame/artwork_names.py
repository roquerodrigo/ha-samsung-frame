"""Names of the artworks uploaded to a TV."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.storage import Store

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import SamsungFrameArtworkNamesData

STORAGE_VERSION = 1


class SamsungFrameArtworkNames:
    """
    Keep a human-readable name for each artwork of one TV.

    The TV identifies personal photos only by the content id it assigns
    (``MY_F0017``) and its Art API has no field for a title, so the names
    live in Home Assistant storage, one file per config entry.
    """

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Bind the names to the storage file of a config entry."""
        self._store: Store[SamsungFrameArtworkNamesData] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}.artwork_names"
        )
        self._names: dict[str, str] = {}

    async def async_load(self) -> None:
        """Read the stored names."""
        stored = await self._store.async_load()
        self._names = dict(stored["names"]) if stored else {}

    def get(self, content_id: str) -> str | None:
        """Return the name of an artwork, if it has one."""
        return self._names.get(content_id)

    async def async_set(self, content_id: str, name: str) -> None:
        """Name an artwork and persist it."""
        self._names[content_id] = name
        await self._async_save()

    async def async_remove(self, content_id: str) -> None:
        """Forget the name of an artwork that no longer exists."""
        if self._names.pop(content_id, None) is not None:
            await self._async_save()

    async def async_delete_storage(self) -> None:
        """Delete the storage file once the entry is removed."""
        await self._store.async_remove()

    async def _async_save(self) -> None:
        await self._store.async_save({"names": dict(self._names)})
