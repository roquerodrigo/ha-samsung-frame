from __future__ import annotations

import pytest

from custom_components.samsung_frame.services.artwork_name import (
    suggested_artwork_name,
)


@pytest.mark.parametrize(
    ("media_content_id", "title", "expected"),
    [
        (
            "media-source://media_source/local/frame.jpg",
            "  Shown title ",
            "Shown title",
        ),
        (
            "media-source://media_source/local/paintings/starry_night.jpg",
            None,
            "starry_night",
        ),
        ("media-source://media_source/local/My%20Garden.png", "", "My Garden"),
        ("https://example.com/art/sunset.jpg?size=large", None, "sunset"),
        (
            (
                "media-source://samsung_frame/artwork/"
                "Claude%20Monet%20-%20Impression%20sunrise%20-%20reframed-1789887454968.jpg"
            ),
            None,
            "Impression sunrise (Claude Monet)",
        ),
        (
            (
                "media-source://samsung_frame/artwork/"
                "Pablo%20Picasso%20-%20The%20Weeping%20Woman%20-%20portrait%20-%20reframed.jpg"
            ),
            None,
            "The Weeping Woman - portrait (Pablo Picasso)",
        ),
        ("media-source://samsung_frame/artwork/Untitled.jpg", None, "Untitled"),
        ("https://example.com/", None, None),
    ],
)
def test_suggested_artwork_name(media_content_id, title, expected):
    assert suggested_artwork_name(media_content_id, title) == expected


def test_no_name_when_nothing_is_left():
    assert suggested_artwork_name("https:///", None) is None
