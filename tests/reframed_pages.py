from __future__ import annotations

CDN = "https://cdn.reframed.gallery/cdn-cgi/image/width=700,quality=80,format=auto"


def tile(path: str, title: str, file_name: str) -> str:
    return (
        f'<div class="Tile-module__tile"><a class="Tile-module__link" href="{path}">'
        f'<div class="Tile-module__blur" style="background-image:url(x)"></div>'
        f'<img class="Tile-module__image" src="{CDN}/originals/{file_name}" '
        f'alt="{title}"/></a><button aria-label="Download {title}">'
        f"<svg></svg></button></div>"
    )


def page(heading: str, *tiles: str, extra: str = "") -> str:
    return (
        '<html><body><a href="/"><img src="/logo.svg" alt="Reframed"/></a>'
        f"<main><h1>{heading}<span>12 artworks</span></h1>{extra}{''.join(tiles)}"
        "</main></body></html>"
    )


MONET_SUNRISE = "Claude%20Monet%20-%20Impression%20sunrise%20-%20reframed-1789.jpg"
MONET_WISTERIA = "Claude%20Monet%20-%20Wisteria%20-%20reframed.png"
HOMER_GULF = "Winslow%20Homer%20-%20The%20Gulf%20Stream%20-%20reframed.jpg"

RECENT = page(
    "Recently Added",
    tile("/claude-monet/impression-sunrise", "Impression, Sunrise", MONET_SUNRISE),
    tile("/winslow-homer/the-gulf-stream", "The Gulf Stream", HOMER_GULF),
    tile("/claude-monet/impression-sunrise", "Impression, Sunrise", MONET_SUNRISE),
    tile("/collections/after-the-storm", "After the Storm", HOMER_GULF),
    tile("/claude-monet/study", "Study", "source/Claude%20Monet%20-%20Study.jpg"),
)

COLLECTIONS = page(
    "Collections",
    tile("/collections/after-the-storm", "After the Storm", HOMER_GULF),
    tile("/collections/in-bloom", "In Bloom", MONET_WISTERIA),
    tile("/claude-monet", "Claude Monet", MONET_SUNRISE),
)

AFTER_THE_STORM = page(
    "After the Storm",
    tile("/winslow-homer/the-gulf-stream", "The Gulf Stream", HOMER_GULF),
)

ARTIST_TABS = (
    '<nav><a href="/artists">A to C</a><a href="/artists/page/2">D to F</a></nav>'
    '<nav><a href="/artists">A to C</a><a href="/artists/page/2">D to F</a>'
    '<a href="/artists/page/2"></a></nav>'
)

ARTISTS_A_C = page(
    "Artists",
    tile("/claude-monet", "Claude Monet", MONET_SUNRISE),
    tile("/claude-monet", "Claude Monet", MONET_WISTERIA),
    tile("/recent", "Recent", HOMER_GULF),
    extra=ARTIST_TABS,
)

ARTISTS_D_F = page(
    "Artists",
    tile("/winslow-homer", "Winslow Homer", HOMER_GULF),
    extra=ARTIST_TABS,
)

MONET = page(
    "Claude Monet",
    tile("/claude-monet/impression-sunrise", "Impression, Sunrise", MONET_SUNRISE),
    tile("/claude-monet/wisteria", "Wisteria", MONET_WISTERIA),
    tile("/winslow-homer/the-gulf-stream", "The Gulf Stream", HOMER_GULF),
)

WITHOUT_HEADING = "<html><body><main></main></body></html>"
