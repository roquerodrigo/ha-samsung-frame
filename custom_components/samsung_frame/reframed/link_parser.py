"""Extract the text links of a Reframed Gallery page."""

from __future__ import annotations

from html.parser import HTMLParser


class ReframedLinkParser(HTMLParser):
    """Collect the target and visible text of every link on the page."""

    def __init__(self) -> None:
        """Initialize an empty parser."""
        super().__init__(convert_charrefs=True)
        self._current_link: str | None = None
        self._current_text: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Start collecting the text of a link."""
        if tag == "a":
            self._current_link = dict(attrs).get("href")
            self._current_text = []

    def handle_data(self, data: str) -> None:
        """Accumulate the text inside the open link."""
        if self._current_link is not None:
            self._current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        """Record the finished link."""
        if tag == "a" and self._current_link is not None:
            text = " ".join("".join(self._current_text).split())
            self.links.append((self._current_link, text))
            self._current_link = None
