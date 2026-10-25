"""Extract the heading and the linked image tiles of a Reframed Gallery page."""

from __future__ import annotations

from html.parser import HTMLParser

from ..data import ReframedTile

_CDN_HOST = "cdn.reframed.gallery"


class ReframedPageParser(HTMLParser):
    """
    Collect the page heading and every gallery image wrapped in a link.

    Artworks, artists and collections are all rendered as the same tile — a
    link around a CDN image whose ``alt`` is the caption — so one parser
    serves every listing page. Only the link target, the ``alt`` text, the
    image URL and the first text of the ``h1`` are read, which keeps it
    independent of the generated CSS class names.
    """

    def __init__(self) -> None:
        """Initialize an empty parser."""
        super().__init__(convert_charrefs=True)
        self._current_link: str | None = None
        self._inside_heading = False
        self.heading: str | None = None
        self.tiles: list[ReframedTile] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Track the open link and heading, and record the gallery images."""
        attributes = dict(attrs)
        if tag == "h1":
            self._inside_heading = True
            return
        if tag == "a":
            self._current_link = attributes.get("href")
            return
        image_source = attributes.get("src")
        title = attributes.get("alt")
        if (
            tag == "img"
            and self._current_link
            and image_source
            and title
            and _CDN_HOST in image_source
        ):
            self.tiles.append(
                ReframedTile(
                    path=self._current_link,
                    title=title.strip(),
                    image_source=image_source,
                )
            )

    def handle_data(self, data: str) -> None:
        """Keep the first text of the heading, which names the page."""
        if self._inside_heading and self.heading is None and data.strip():
            self.heading = data.strip()

    def handle_endtag(self, tag: str) -> None:
        """Forget the link or heading once it closes."""
        if tag == "a":
            self._current_link = None
        elif tag == "h1":
            self._inside_heading = False
