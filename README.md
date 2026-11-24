# Samsung The Frame

<!-- ha-marketplace:exclude-start -->
[![CI](https://github.com/roquerodrigo/ha-samsung-frame/actions/workflows/ci.yml/badge.svg)](https://github.com/roquerodrigo/ha-samsung-frame/actions/workflows/ci.yml)
[![GitHub release](https://img.shields.io/github/v/release/roquerodrigo/ha-samsung-frame)](https://github.com/roquerodrigo/ha-samsung-frame/releases/latest)
[![Sponsor](https://img.shields.io/badge/Sponsor-%E2%9D%A4-db61a2?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/roquerodrigo)

[![Open your Home Assistant instance and open a repository in the Marketplace.](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=roquerodrigo&repository=ha-samsung-frame&category=integration)
<!-- ha-marketplace:exclude-end -->

Put your own pictures on a [Samsung The Frame](https://www.samsung.com/us/televisions-home-theater/tvs/the-frame/)
TV from Home Assistant, pick artworks from the free
[Reframed Gallery](https://www.reframed.gallery/) collection, and switch
between art and regular TV from your automations. Home Assistant talks to the
TV on your local network, so nothing goes through the SmartThings cloud.

## Features

- Send a photo from your media folder, an image entity or any web address to
  the TV, with or without a matte, and show it right away.
- Browse Reframed Gallery in the Home Assistant media browser, by recent
  additions, collection or artist, and send any artwork to the TV.
- Turn Art Mode on and off, and see which artwork the TV is showing.
- Give every artwork a readable name instead of the ID the TV assigns, such as
  `MY_F0017`. Uploads are named after the picture they came from.
- Select or delete any artwork in the collection of the TV.
- Works next to the Samsung Smart TV integration of Home Assistant. A TV that
  is already paired with it accepts this integration without asking again.

## Requirements

- Home Assistant 2026.10.3 or newer.
- A Samsung The Frame TV on the same network as Home Assistant. The setup
  checks that the TV supports Art Mode.
- Internet access from Home Assistant, only for Reframed Gallery and for
  pictures given by web address.

<!-- ha-marketplace:exclude-start -->
## Installation

### Home Assistant Marketplace (recommended)

1. Select the **Open your Home Assistant instance** button above, or go to
   **Settings → Marketplace**, select **Add from link** in the upper right
   corner, enter `roquerodrigo/ha-samsung-frame` and select **Add**.
2. Select **Install**.
3. Restart Home Assistant.

The Marketplace comes with Home Assistant 2026.11 and later. On older
versions, add this repository to HACS as a custom repository of type
**Integration** and install it from there.

### Manual

1. Download `samsung_frame.zip` from the
   [latest release](https://github.com/roquerodrigo/ha-samsung-frame/releases/latest).
2. Extract it into `config/custom_components/samsung_frame/`.
3. Restart Home Assistant.
<!-- ha-marketplace:exclude-end -->

## Configuration

Turn the TV on. Then go to **Settings → Devices & services → Add integration**,
search for **Samsung The Frame** and fill in the form.

| Field | What to enter                        |
|-------|--------------------------------------|
| Host  | The IP address or hostname of the TV |

Home Assistant then asks you to pair. Select **Submit** and, within 30
seconds, accept the connection request that appears on the TV.

To point the integration at a new address of the same TV, open it and select
**Reconfigure**. If the TV stops accepting the pairing, Home Assistant shows a
notice: open it, select **Submit** and accept the request on the TV again.

## Options

Open the integration and select **Configure**.

| Setting                    | Default | Range                      | Effect                                                                     |
|----------------------------|---------|----------------------------|----------------------------------------------------------------------------|
| Polling interval (seconds) | 30      | 10 or more, in steps of 10 | How often Home Assistant reads the Art Mode state and the current artwork. |

## Entities

| Entity          | Type   | Shows                                                                                     |
|-----------------|--------|-------------------------------------------------------------------------------------------|
| Art mode        | Switch | On while the TV shows art. Turn it on or off to switch between art and regular TV.        |
| Current artwork | Sensor | The name of the selected artwork, or its content ID when it has no name. The **Content ID** attribute always holds the ID. |

Both entities are unavailable while the TV is off.

## Reframed Gallery

[Reframed Gallery](https://www.reframed.gallery/) is a free collection of
paintings and photographs extended to fill the 16:9 screen of the TV. Open
**Media → Reframed Gallery** to browse it:

- **Recent**: the latest additions.
- **Collections**: the curated collections of the site.
- **Artists**: every artist, grouped alphabetically as on the site.

Artworks show as `Title (Artist)`. You can also pick them in the **Image**
field of the Upload artwork action, and the upload is named after the artwork.

Reframed Gallery offers its artworks for personal use only (see its
[FAQ](https://www.reframed.gallery/faq)). The site is run by one person. If you
enjoy it, consider [sending a tip](https://ko-fi.com/O5O51FWPUL).

## Actions

Every action has a **TV** field (`config_entry_id`) that picks the TV. In the
action editor it is a list of your TVs. To use an action in YAML, pick the TV
in the editor and switch to YAML mode to see its ID.

The content ID of an artwork is returned by Upload artwork and shown in the
**Content ID** attribute of the Current artwork sensor.

### Upload artwork

`samsung_frame.upload_artwork` sends a JPEG or PNG picture to the collection of
the TV and returns its content ID.

| Field       | Key               | Required | Default   | Description |
|-------------|-------------------|----------|-----------|-------------|
| TV          | `config_entry_id` | yes      |           | The TV to upload to. |
| Image       | `image`           | yes      |           | A picture from the media browser (local media, image entities, Reframed Gallery), or a web address starting with `http://` or `https://` in `media_content_id`. |
| Matte style | `matte_style`     | no       | `none`    | `none`, `modernthin`, `modern`, `modernwide`, `flexible`, `shadowbox`, `panoramic`, `triptych`, `mix` or `squares`. Not every TV supports every style. |
| Matte color | `matte_color`     | no       | `polar`   | `polar`, `black`, `neutral`, `antique`, `warm`, `sand`, `seafoam`, `sage`, `burgandy`, `navy`, `apricot`, `byzantine`, `lavender`, `redorange`, `skyblue` or `turquoise`. Ignored when the style is `none`. |
| Show        | `show`            | no       | `true`    | Show the picture on the TV right after the upload. |
| Name        | `name`            | no       |           | The name Home Assistant shows for the artwork. Without it, the title picked in the media browser is used, then the file name. |

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

The response holds the content ID and the name of the new artwork
(`uploaded.content_id` and `uploaded.name`). Home Assistant sends the picture
as it is, without resizing or cropping, so pictures in the 16:9 format of the
screen look best.

### Select artwork

`samsung_frame.select_artwork` selects an artwork that is already in the
collection of the TV.

| Field      | Key               | Required | Default | Description |
|------------|-------------------|----------|---------|-------------|
| TV         | `config_entry_id` | yes      |         | The TV to use. |
| Content ID | `content_id`      | yes      |         | The artwork to select, for example `MY_F0001`. |
| Show       | `show`            | no       | `true`  | Show the artwork on the TV right away. |

```yaml
action: samsung_frame.select_artwork
data:
  config_entry_id: 01J0000000000000000000000
  content_id: MY_F0001
```

### Rename artwork

`samsung_frame.rename_artwork` changes the name Home Assistant shows for an
artwork. The TV itself keeps no names, so this also works for photos added
from the SmartThings app.

| Field      | Key               | Required | Default | Description |
|------------|-------------------|----------|---------|-------------|
| TV         | `config_entry_id` | yes      |         | The TV to use. |
| Content ID | `content_id`      | yes      |         | The artwork to rename, for example `MY_F0017`. |
| Name       | `name`            | yes      |         | The new name. An empty name removes it, and the sensor shows the content ID again. |

```yaml
action: samsung_frame.rename_artwork
data:
  config_entry_id: 01J0000000000000000000000
  content_id: MY_F0017
  name: Impression, Sunrise (Claude Monet)
```

### Delete artwork

`samsung_frame.delete_artwork` removes an artwork from the collection of the
TV, together with its name.

| Field      | Key               | Required | Default | Description |
|------------|-------------------|----------|---------|-------------|
| TV         | `config_entry_id` | yes      |         | The TV to use. |
| Content ID | `content_id`      | yes      |         | The artwork to delete, for example `MY_F0001`. |

```yaml
action: samsung_frame.delete_artwork
data:
  config_entry_id: 01J0000000000000000000000
  content_id: MY_F0001
```

To change a daily picture without filling the storage of the TV, keep the
content ID returned by Upload artwork and delete that artwork before the next
upload.

## How it works

Home Assistant reads the Art Mode state and the current artwork from the TV at
every polling interval, over your local network. The switch and the actions
that change the TV talk to it directly, one request at a time, and the entities
update right after.

Pictures from your local media are read from disk. Other pictures, including
Reframed Gallery artworks, are downloaded by Home Assistant and then sent to
the TV. The TV never needs internet access for this.

Reframed Gallery is read from the public pages of the site. Each page is kept
for an hour, so browsing back and forth does not load the site again.

Artwork names are stored in Home Assistant, one list per TV, and are removed
when you delete the integration.

A firmware update can change the identifier the TV reports. Home Assistant
recognizes the TV by its MAC address and keeps the same device, entities and
history.

## Troubleshooting

**The entities are unavailable.** The TV only answers while it is on or showing
art. Turn it on and the entities come back at the next update.

**Pairing times out.** Make sure the TV is on, select **Submit** again and
accept the request on the TV screen. If you denied it before, allow
`HomeAssistant` again on the TV under **Settings → General → External Device
Manager → Device Connection Manager → Device List**.

**The entities stay unavailable although the TV is on.** The art service of
the TV can stop answering after a long time on. Home Assistant gives up on each
request instead of waiting, so it keeps working normally. Unplug the TV for 30
seconds to bring the service back.

**Home Assistant asks to pair again.** The TV no longer trusts Home Assistant.
Open the notice, select **Submit** and accept the request on the TV.

**An upload fails with "Only JPEG and PNG images can be uploaded".** The TV
integration uploads only these two formats. Convert the picture first.

**Something else is wrong.** Download the diagnostics from the integration's
menu and attach them to an
[issue](https://github.com/roquerodrigo/ha-samsung-frame/issues). The pairing
token and the MAC address are removed from the file. Debug logging also turns
on the logs of the library that talks to the TV, which contain the pairing
token. Remove it from the log before you share it.

## Known limitations

- The integration does not turn the TV on or off. The Samsung Smart TV
  integration of Home Assistant covers power and the remote.
- Artwork names live only in Home Assistant. The TV and the SmartThings app do
  not see them.

## Support

This integration is built and maintained on personal time, on hardware bought
for the purpose. If it is useful to you, consider
[sponsoring the work](https://github.com/sponsors/roquerodrigo). It keeps the
devices, the testing and the releases coming.

Report bugs and request features in the
[issue tracker](https://github.com/roquerodrigo/ha-samsung-frame/issues).

<!-- ha-marketplace:exclude-start -->
## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the development setup and
workflow, and [CODE_STYLE.md](CODE_STYLE.md) for the code conventions.

## License

[MIT](LICENSE)
<!-- ha-marketplace:exclude-end -->
