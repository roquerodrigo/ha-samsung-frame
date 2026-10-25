# Samsung The Frame

[![CI](https://github.com/roquerodrigo/ha-samsung-frame/actions/workflows/ci.yml/badge.svg)](https://github.com/roquerodrigo/ha-samsung-frame/actions/workflows/ci.yml)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

[![Sponsor](https://img.shields.io/badge/Sponsor-%E2%9D%A4-db61a2?logo=githubsponsors&logoColor=white&style=for-the-badge)](https://github.com/sponsors/roquerodrigo)

[![Open your Home Assistant instance and open the repository inside HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=roquerodrigo&repository=ha-samsung-frame&category=integration)

---

Home Assistant integration for the Art Mode of [Samsung The Frame](https://www.samsung.com/us/televisions-home-theater/tvs/the-frame/) TVs. Upload your own images to the TV and show them as artwork, switch Art Mode on and off, and manage the art collection — all over the local network, without the SmartThings cloud.

## Features

- **Upload artwork** from any Home Assistant media source (local media, image entities) or an HTTP(S) URL, with an optional matte, and show it right away.
- **[Reframed Gallery](https://www.reframed.gallery/) in the media browser**: thousands of artworks prepared for The Frame, browsable by recent additions, collection and artist, and ready to upload.
- **Art Mode switch** to move between art and regular TV content.
- **Current artwork sensor** with the name of the artwork the TV has selected.
- **Artwork names**: the TV only knows its own IDs (`MY_F0017`), so the integration names every upload after the media it came from, and any artwork can be renamed.
- **Select** and **delete** artworks of the collection by content ID.

## Requirements

- A Samsung The Frame TV on the same network as Home Assistant.
- Home Assistant 2026.10.3 or newer.

## Installation

### HACS

1. Open HACS with the button above, or add `https://github.com/roquerodrigo/ha-samsung-frame` as a custom repository of type **Integration**.
2. Install **Samsung The Frame** and restart Home Assistant.

### Manual

Copy `custom_components/samsung_frame` into the `custom_components` directory of your Home Assistant configuration and restart Home Assistant.

## Configuration

1. Go to **Settings → Devices & services → Add integration** and pick **Samsung The Frame**.
2. Enter the IP address or hostname of the TV. The TV has to be on.
3. Select **Submit** and accept the connection request that appears on the TV within 30 seconds. A TV already paired with the core Samsung Smart TV integration accepts the connection without asking.

The polling interval (30 seconds by default) can be changed in the integration options.

## Entities

| Entity | Description |
| --- | --- |
| Art mode (switch) | On while the TV shows art. Turning it on or off switches the TV between art and regular content. |
| Current artwork (sensor) | Name of the artwork currently selected, for example `Impression, Sunrise (Claude Monet)`. Artworks without a name show their content ID (`MY_F0004`), which is also available in the `content_id` attribute. |

## Reframed Gallery

Once the integration is set up, **Media → Reframed Gallery** lists the artworks of [Reframed Gallery](https://www.reframed.gallery/), a free collection of paintings and photographs extended to fill a 16:9 screen:

- **Recent** — the latest additions.
- **Collections** — the curated collections of the site.
- **Artists** — every artist, grouped alphabetically as on the site.

Every artwork is a 3840×2160 image, so it can be picked directly in the `image` field of `samsung_frame.upload_artwork`:

```yaml
action: samsung_frame.upload_artwork
data:
  config_entry_id: 01J0000000000000000000000
  image:
    media_content_id: media-source://samsung_frame/artwork/Claude%20Monet%20-%20Impression%20sunrise%20-%20reframed-1789887454968.jpg
    media_content_type: image/jpeg
```

Reframed Gallery provides its artworks **for personal use only**; see its [FAQ](https://www.reframed.gallery/faq). The site is maintained by one person — if you enjoy it, consider [sending a tip](https://ko-fi.com/O5O51FWPUL). The integration reads the public pages of the site and caches each one for an hour.

## Actions

### `samsung_frame.upload_artwork`

Uploads a JPEG or PNG image to the art collection of the TV and returns its content ID.

| Field | Required | Description |
| --- | --- | --- |
| `config_entry_id` | yes | The TV to upload to. |
| `image` | yes | The image, picked from the media browser (local media, image entities) or given as an HTTP(S) URL in `media_content_id`. |
| `matte_style` | no | `none` (default), `modernthin`, `modern`, `modernwide`, `flexible`, `shadowbox`, `panoramic`, `triptych`, `mix` or `squares`. Not every TV supports every style. |
| `matte_color` | no | Color of the matte, `polar` by default. Ignored when the style is `none`. |
| `show` | no | Select the uploaded artwork as the one on display. Defaults to `true`. |
| `name` | no | Name shown for the artwork. Defaults to the title picked in the media browser, then to the file name (`Title (Artist)` for Reframed Gallery artworks). |

```yaml
action: samsung_frame.upload_artwork
data:
  config_entry_id: 01J0000000000000000000000
  image:
    media_content_id: media-source://media_source/local/paintings/starry_night.jpg
    media_content_type: image/jpeg
  matte_style: modern
  matte_color: polar
response_variable: uploaded
```

The response holds the content ID and the name of the new artwork (`uploaded.content_id`, `uploaded.name`). Images are shown as uploaded; for the best result use 3840×2160 pictures.

### `samsung_frame.select_artwork`

Selects an artwork of the collection by `content_id`. With `show: true` (default) it becomes the artwork on display.

### `samsung_frame.rename_artwork`

Changes the name shown for an artwork, by `content_id`. The TV itself keeps no names — they are stored by Home Assistant — so this also names photos uploaded from the SmartThings app. A blank `name` goes back to the content ID.

```yaml
action: samsung_frame.rename_artwork
data:
  config_entry_id: 01J0000000000000000000000
  content_id: MY_F0017
  name: Impression, Sunrise (Claude Monet)
```

### `samsung_frame.delete_artwork`

Deletes an artwork from the collection by `content_id`, together with its name. Combine it with the response of `upload_artwork` to replace a daily picture without filling the storage of the TV.

## Troubleshooting

- **The entities are unavailable while the TV is off.** The Art Mode API only answers while the TV is on or showing art.
- **Pairing times out.** Make sure the TV is on, select Submit again and accept the request on the TV screen. If you denied it once, allow `HomeAssistant` again under **Settings → General → External Device Manager → Device Connection Manager → Device List** on the TV.
- Enable debug logging for `custom_components.samsung_frame` and attach the diagnostics dump when opening an issue.

## Development

Conventions for contributors live in [`CODE_STYLE.md`](./CODE_STYLE.md); architectural notes for AI agents in [`CLAUDE.md`](./CLAUDE.md).

```bash
scripts/setup                                  # create .venv and install deps (uv sync)
scripts/develop                                # start Home Assistant in debug mode with the integration loaded
scripts/lint                                   # ruff format, ruff check, mypy and pytest (90 % coverage gate)
```

## License

[MIT](./LICENSE)
