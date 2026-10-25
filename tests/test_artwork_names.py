from __future__ import annotations

from homeassistant.config_entries import ConfigEntryState

from custom_components.samsung_frame.artwork_names import SamsungFrameArtworkNames


async def test_names_persist_across_instances(hass, hass_storage):
    names = SamsungFrameArtworkNames(hass, "entry")
    await names.async_load()
    await names.async_set("MY_F0017", "Impression, Sunrise (Claude Monet)")
    assert hass_storage["samsung_frame.entry.artwork_names"]["data"] == {
        "names": {"MY_F0017": "Impression, Sunrise (Claude Monet)"}
    }

    reloaded = SamsungFrameArtworkNames(hass, "entry")
    await reloaded.async_load()
    assert reloaded.get("MY_F0017") == "Impression, Sunrise (Claude Monet)"


async def test_names_start_empty(hass, hass_storage):
    names = SamsungFrameArtworkNames(hass, "entry")
    await names.async_load()
    assert names.get("MY_F0017") is None


async def test_remove_unknown_name_writes_nothing(hass, hass_storage):
    names = SamsungFrameArtworkNames(hass, "entry")
    await names.async_load()
    await names.async_remove("MY_F0017")
    assert "samsung_frame.entry.artwork_names" not in hass_storage


async def test_remove_forgets_the_name(hass, hass_storage):
    names = SamsungFrameArtworkNames(hass, "entry")
    await names.async_load()
    await names.async_set("MY_F0017", "Sunrise")
    await names.async_remove("MY_F0017")
    assert names.get("MY_F0017") is None
    assert hass_storage["samsung_frame.entry.artwork_names"]["data"] == {"names": {}}


async def test_names_survive_a_reload(hass, setup_integration):
    await setup_integration.runtime_data.artwork_names.async_set("MY_F0004", "Sunrise")
    await hass.config_entries.async_reload(setup_integration.entry_id)
    await hass.async_block_till_done()
    assert setup_integration.state == ConfigEntryState.LOADED
    assert setup_integration.runtime_data.artwork_names.get("MY_F0004") == "Sunrise"
    assert hass.states.get("sensor.living_room_tv_current_artwork").state == "Sunrise"


async def test_removing_the_entry_deletes_the_names(
    hass, setup_integration, hass_storage
):
    await setup_integration.runtime_data.artwork_names.async_set("MY_F0004", "Sunrise")
    key = f"samsung_frame.{setup_integration.entry_id}.artwork_names"
    assert key in hass_storage
    await hass.config_entries.async_remove(setup_integration.entry_id)
    await hass.async_block_till_done()
    assert key not in hass_storage
