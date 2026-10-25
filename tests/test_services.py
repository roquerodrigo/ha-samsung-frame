from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from custom_components.samsung_frame.const import DOMAIN
from custom_components.samsung_frame.data import SamsungFrameArtworkImage
from custom_components.samsung_frame.exceptions import (
    SamsungFrameApiClientCommunicationError,
)

IMAGE = SamsungFrameArtworkImage(content=b"\xff\xd8\xffjpeg", file_type="jpg")
MEDIA = {
    "media_content_id": "media-source://media_source/local/frame.jpg",
    "media_content_type": "image/jpeg",
}


@pytest.fixture
def image_loader():
    with patch(
        "custom_components.samsung_frame.services.upload_artwork."
        "SamsungFrameArtworkImageLoader.async_load",
        AsyncMock(return_value=IMAGE),
    ) as async_load:
        yield async_load


async def _call(hass, service, data, *, return_response=False):
    return await hass.services.async_call(
        DOMAIN, service, data, blocking=True, return_response=return_response
    )


async def test_upload_returns_content_id(
    hass, setup_integration, mock_api_client, image_loader
):
    response = await _call(
        hass,
        "upload_artwork",
        {"config_entry_id": setup_integration.entry_id, "image": MEDIA},
        return_response=True,
    )
    assert response == {"content_id": "MY_F0020", "name": "frame"}
    image_loader.assert_awaited_once_with(MEDIA["media_content_id"])
    mock_api_client.async_upload_artwork.assert_awaited_once_with(
        IMAGE, "none", show=True
    )


async def test_upload_without_response(
    hass, setup_integration, mock_api_client, image_loader
):
    response = await _call(
        hass,
        "upload_artwork",
        {"config_entry_id": setup_integration.entry_id, "image": MEDIA},
    )
    assert response is None
    mock_api_client.async_upload_artwork.assert_awaited_once()


async def test_upload_combines_matte_style_and_color(
    hass, setup_integration, mock_api_client, image_loader
):
    await _call(
        hass,
        "upload_artwork",
        {
            "config_entry_id": setup_integration.entry_id,
            "image": MEDIA,
            "matte_style": "shadowbox",
            "matte_color": "navy",
            "show": False,
        },
    )
    mock_api_client.async_upload_artwork.assert_awaited_once_with(
        IMAGE, "shadowbox_navy", show=False
    )


async def test_upload_ignores_color_without_matte(
    hass, setup_integration, mock_api_client, image_loader
):
    await _call(
        hass,
        "upload_artwork",
        {
            "config_entry_id": setup_integration.entry_id,
            "image": MEDIA,
            "matte_color": "navy",
        },
    )
    assert mock_api_client.async_upload_artwork.await_args.args[1] == "none"


async def test_upload_refreshes_state(
    hass, setup_integration, mock_api_client, image_loader
):
    mock_api_client.async_get_art_state.return_value = {
        "art_mode": True,
        "current_artwork_id": "MY_F0020",
    }
    await _call(
        hass,
        "upload_artwork",
        {"config_entry_id": setup_integration.entry_id, "image": MEDIA},
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.living_room_tv_current_artwork")
    assert state.state == "frame"
    assert state.attributes["content_id"] == "MY_F0020"


async def test_upload_failure_raises_translated_error(
    hass, setup_integration, mock_api_client, image_loader
):
    mock_api_client.async_upload_artwork.side_effect = (
        SamsungFrameApiClientCommunicationError("down")
    )
    with pytest.raises(HomeAssistantError) as error:
        await _call(
            hass,
            "upload_artwork",
            {"config_entry_id": setup_integration.entry_id, "image": MEDIA},
        )
    assert error.value.translation_key == "upload_failed"


async def test_upload_rejects_unknown_matte(hass, setup_integration, image_loader):
    with pytest.raises(Exception, match="matte_style"):
        await _call(
            hass,
            "upload_artwork",
            {
                "config_entry_id": setup_integration.entry_id,
                "image": MEDIA,
                "matte_style": "baroque",
            },
        )


async def test_unknown_entry_is_rejected(hass, setup_integration, image_loader):
    with pytest.raises(ServiceValidationError) as error:
        await _call(
            hass, "upload_artwork", {"config_entry_id": "missing", "image": MEDIA}
        )
    assert error.value.translation_key == "entry_not_found"


async def test_unloaded_entry_is_rejected(hass, setup_integration, image_loader):
    await hass.config_entries.async_unload(setup_integration.entry_id)
    with pytest.raises(ServiceValidationError) as error:
        await _call(
            hass,
            "select_artwork",
            {"config_entry_id": setup_integration.entry_id, "content_id": "MY_F0004"},
        )
    assert error.value.translation_key == "entry_not_loaded"


async def test_select_artwork(hass, setup_integration, mock_api_client):
    await _call(
        hass,
        "select_artwork",
        {"config_entry_id": setup_integration.entry_id, "content_id": "MY_F0008"},
    )
    mock_api_client.async_select_artwork.assert_awaited_once_with("MY_F0008", show=True)


async def test_select_failure_raises_translated_error(
    hass, setup_integration, mock_api_client
):
    mock_api_client.async_select_artwork.side_effect = (
        SamsungFrameApiClientCommunicationError("down")
    )
    with pytest.raises(HomeAssistantError) as error:
        await _call(
            hass,
            "select_artwork",
            {"config_entry_id": setup_integration.entry_id, "content_id": "MY_F0008"},
        )
    assert error.value.translation_key == "select_failed"
    assert error.value.translation_placeholders == {"content_id": "MY_F0008"}


async def test_delete_artwork(hass, setup_integration, mock_api_client):
    await _call(
        hass,
        "delete_artwork",
        {"config_entry_id": setup_integration.entry_id, "content_id": "MY_F0008"},
    )
    mock_api_client.async_delete_artwork.assert_awaited_once_with("MY_F0008")


async def test_delete_failure_raises_translated_error(
    hass, setup_integration, mock_api_client
):
    mock_api_client.async_delete_artwork.side_effect = (
        SamsungFrameApiClientCommunicationError("down")
    )
    with pytest.raises(HomeAssistantError) as error:
        await _call(
            hass,
            "delete_artwork",
            {"config_entry_id": setup_integration.entry_id, "content_id": "MY_F0008"},
        )
    assert error.value.translation_key == "delete_failed"


async def test_upload_prefers_the_given_name(
    hass, setup_integration, mock_api_client, image_loader
):
    response = await _call(
        hass,
        "upload_artwork",
        {
            "config_entry_id": setup_integration.entry_id,
            "image": {**MEDIA, "metadata": {"title": "Browser title"}},
            "name": "Living room sunrise",
        },
        return_response=True,
    )
    assert response["name"] == "Living room sunrise"
    names = setup_integration.runtime_data.artwork_names
    assert names.get("MY_F0020") == "Living room sunrise"


async def test_upload_uses_the_media_browser_title(
    hass, setup_integration, mock_api_client, image_loader
):
    await _call(
        hass,
        "upload_artwork",
        {
            "config_entry_id": setup_integration.entry_id,
            "image": {
                **MEDIA,
                "metadata": {"title": "Impression, Sunrise (Claude Monet)"},
            },
        },
    )
    names = setup_integration.runtime_data.artwork_names
    assert names.get("MY_F0020") == "Impression, Sunrise (Claude Monet)"


async def test_upload_without_any_name_stores_nothing(
    hass, setup_integration, mock_api_client, image_loader
):
    response = await _call(
        hass,
        "upload_artwork",
        {
            "config_entry_id": setup_integration.entry_id,
            "image": {
                "media_content_id": "https:///",
                "media_content_type": "image/jpeg",
            },
        },
        return_response=True,
    )
    assert response == {"content_id": "MY_F0020", "name": None}
    assert setup_integration.runtime_data.artwork_names.get("MY_F0020") is None


async def test_delete_forgets_the_name(hass, setup_integration, mock_api_client):
    names = setup_integration.runtime_data.artwork_names
    await names.async_set("MY_F0008", "Garden")
    await _call(
        hass,
        "delete_artwork",
        {"config_entry_id": setup_integration.entry_id, "content_id": "MY_F0008"},
    )
    assert names.get("MY_F0008") is None


async def test_failed_delete_keeps_the_name(hass, setup_integration, mock_api_client):
    names = setup_integration.runtime_data.artwork_names
    await names.async_set("MY_F0008", "Garden")
    mock_api_client.async_delete_artwork.side_effect = (
        SamsungFrameApiClientCommunicationError("down")
    )
    with pytest.raises(HomeAssistantError):
        await _call(
            hass,
            "delete_artwork",
            {"config_entry_id": setup_integration.entry_id, "content_id": "MY_F0008"},
        )
    assert names.get("MY_F0008") == "Garden"


async def test_rename_updates_the_sensor_right_away(hass, setup_integration):
    await _call(
        hass,
        "rename_artwork",
        {
            "config_entry_id": setup_integration.entry_id,
            "content_id": "MY_F0004",
            "name": "  Sunset over the bay  ",
        },
    )
    state = hass.states.get("sensor.living_room_tv_current_artwork")
    assert state.state == "Sunset over the bay"
    assert state.attributes["content_id"] == "MY_F0004"


async def test_blank_rename_goes_back_to_the_content_id(hass, setup_integration):
    names = setup_integration.runtime_data.artwork_names
    await names.async_set("MY_F0004", "Sunset")
    await _call(
        hass,
        "rename_artwork",
        {
            "config_entry_id": setup_integration.entry_id,
            "content_id": "MY_F0004",
            "name": " ",
        },
    )
    assert names.get("MY_F0004") is None
    assert hass.states.get("sensor.living_room_tv_current_artwork").state == "MY_F0004"
