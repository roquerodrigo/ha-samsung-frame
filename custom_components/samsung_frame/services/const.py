"""Names and fixed options of the integration-level actions."""

from __future__ import annotations

SERVICE_UPLOAD_ARTWORK: str = "upload_artwork"
SERVICE_SELECT_ARTWORK: str = "select_artwork"
SERVICE_DELETE_ARTWORK: str = "delete_artwork"
SERVICE_RENAME_ARTWORK: str = "rename_artwork"

ATTR_CONFIG_ENTRY_ID: str = "config_entry_id"
ATTR_IMAGE: str = "image"
ATTR_MATTE_STYLE: str = "matte_style"
ATTR_MATTE_COLOR: str = "matte_color"
ATTR_SHOW: str = "show"
ATTR_CONTENT_ID: str = "content_id"
ATTR_NAME: str = "name"

MATTE_STYLE_NONE: str = "none"
MATTE_STYLES: tuple[str, ...] = (
    MATTE_STYLE_NONE,
    "modernthin",
    "modern",
    "modernwide",
    "flexible",
    "shadowbox",
    "panoramic",
    "triptych",
    "mix",
    "squares",
)
MATTE_COLORS: tuple[str, ...] = (
    "polar",
    "black",
    "neutral",
    "antique",
    "warm",
    "sand",
    "seafoam",
    "sage",
    "burgandy",
    "navy",
    "apricot",
    "byzantine",
    "lavender",
    "redorange",
    "skyblue",
    "turquoise",
)
