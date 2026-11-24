# CLAUDE.md

Guidance for Claude Code (claude.ai/code) agents working in this repository.

## Always read `CODE_STYLE.md` first

Before creating, renaming or restructuring any file/class/function, **read [`CODE_STYLE.md`](./CODE_STYLE.md)**. It is the single source of truth for conventions: language, file organisation, naming, typing, properties vs `__init__`, imports, docstrings, comments, coordinator pattern, diagnostics and actions layout, translations, lint workflow.

For user-facing topics (features, installation, configuration, entities, actions), see [`README.md`](./README.md); for the development setup and commands, see [`CONTRIBUTING.md`](./CONTRIBUTING.md).

This file deliberately avoids restating those rules — it only adds:

1. The verification workflow agents must run after every change.
2. The architectural reasoning that is not obvious from `CODE_STYLE.md` alone.
3. Where the repository came from.

## Origin

This repository was generated from `ha-integration-blueprint`. The copy was one-time and one-directional: blueprint changes do not flow here automatically, so a convention or CI change made there only arrives if it is ported by hand.

## Verification workflow

**After every code change, always run lint then tests, in that order, before declaring the task done. Either run `scripts/lint` (a thin wrapper that only chains the four commands) or run them directly:**

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy custom_components/samsung_frame
uv run pytest
```

- Lint runs `ruff format`, `ruff check` and `mypy` — all configured in `pyproject.toml`. Fix any failure and re-run before moving on.
- `pytest` enforces a **90 % coverage gate** (`--cov-fail-under` in `pyproject.toml`).

Both gates mirror CI (`.github/workflows/ci.yml`). Skip this only when the change literally cannot affect lint or tests (e.g., README-only edits).

## Bumping the Home Assistant version

The Home Assistant version is pinned in two places and **must be updated together**, otherwise CI, HACS and the test harness drift apart:

1. `pyproject.toml` `[dependency-groups] dev` — `homeassistant==<X.Y.Z>` (runtime/CI lint + mypy) **and** `pytest-homeassistant-custom-component==<matching release>` (the test harness ships its own pinned `homeassistant`; the two pins must come from the same HA release, otherwise lint and tests resolve different cores).
2. `hacs.json` — `"homeassistant": "<X.Y.Z>"` (minimum HA core enforced by HACS).

Verify the pairing on PyPI before committing: the `requires_dist` of `pytest-homeassistant-custom-component` must list the same `homeassistant==<X.Y.Z>` you pinned in `pyproject.toml`.

`pytest`, `pytest-asyncio` and `pytest-cov` are not pinned directly: the harness pins them, so they move with it. Dependabot ignores both `homeassistant` and the harness.

## Conventions not obvious from the code

The integration follows the HA `DataUpdateCoordinator` pattern. A few choices are not evident from reading a single file:

- State lives on `entry.runtime_data` (auto-discarded on unload), **never** on `hass.data`.
- `data/__init__.py` holds the `type` alias `SamsungFrameConfigEntry` **and** re-exports every symbol from the sibling modules, so downstream code imports everything from `.data`.
- `samsungtvws` is synchronous. `SamsungFrameApiClient` runs every operation in the executor, opens a fresh Art Mode connection per operation, and serialises them behind an `asyncio.Lock` because the TV handles concurrent art sessions poorly. Upstream exceptions are mapped onto the `exceptions/` hierarchy in `_translated_errors`; nothing above `api.py` catches a `samsungtvws` exception.
- There are no credentials. The config flow reads the device information over REST (no authentication), then opens the `samsung.remote.control` channel for the user to approve on the TV: recent firmware no longer shows the prompt on the Art Mode channel, and only a token issued through the remote control channel opens it. The token is stored on the entry; a TV that already trusts the client name may issue none, and `token: None` is a valid state. The client name is `HomeAssistant`, the same one the core `samsungtv` integration uses, so a TV already paired with core accepts it without a new prompt. The TV keeps a single valid token per client — whatever the name — and revokes it whenever it issues another one, which core does on every reconnection; a revoked token gets `ms.channel.timeOut` on the Art Mode channel while a trusted client without a token is still accepted. `_open_art_channel` therefore retries without the token after that timeout and keeps going without it; only when the tokenless connection is refused too does the timeout map to `SamsungFrameApiClientAuthenticationError` and start the reauth. Presenting a revoked token is not harmless: the TV then revokes the token core holds as well, so core asks for approval on the next start and the cycle repeats on every restart. The coordinator therefore writes `token: None` to the entry once the client dropped it (`_async_forget_revoked_token`), and never presents it again. During pairing the same timeout only means the prompt was not accepted.
- The TV pings the Art Mode channel every six seconds, which restarts the per-read socket timeout of `websocket-client`, and its art service can wedge until the TV is power cycled — it then never sends `ms.channel.ready`. `_deadline` in `api.py` aborts the socket once an operation outlives its timeout, so a wedged TV fails the first refresh with `ConfigEntryNotReady` instead of blocking the bootstrap of Home Assistant.
- Firmware updates can change the identifier the TV reports over REST (the entry's `unique_id`). `SamsungFrameDeviceIdentity` treats a new identifier as the same TV when the MAC address matches the registered device, and `async_setup_entry` moves the entry, the device and the entity unique ids to it. Reconfigure uses the same check instead of `_abort_if_unique_id_mismatch`.
- An `UnauthorizedError` from the TV maps to `SamsungFrameApiClientAuthenticationError`; the coordinator turns it into `ConfigEntryAuthFailed`, which starts the reauth flow — a new pairing, not a password prompt.
- The `upload_artwork` action accepts any media source or an HTTP(S) URL. Local media resolves to a file path and is read from disk; other media sources resolve to a URL served by Home Assistant and are downloaded. Only JPEG and PNG are accepted, detected from the file signature.
- Since HA 2026.10 the device registry no longer merges devices across config entries by connection, so this integration's device stays separate from the one created by the core `samsungtv` integration even though both declare the same MAC address.
- Never enable debug logging for the `samsungtvws` logger in shared logs: it writes the WebSocket URL, token included.
- `media_source.py` exposes Reframed Gallery in the media browser. The site has no public API and `robots.txt` disallows `/api/`, so `reframed/` reads the public HTML pages. Every listing (recent, collections, collection, artist index, artist) renders the same tile — a link around a CDN image whose `alt` is the caption — and `ReframedPageParser` only reads `href`, `src`, `alt` and the first text of the `h1`, never the generated CSS class names. Pages are cached for an hour in `ReframedGalleryClient`; keep it that way, the site is run by a single person.
- An artwork is identified by its percent-encoded file name on the CDN (`artwork/<file>`), which resolves to `https://cdn.reframed.gallery/originals/<file>` without fetching any page. `async_resolve_media` only accepts a single path segment ending in `.jpg`, `.jpeg` or `.png`, so a crafted identifier cannot point the download anywhere else.
- The Art API has no title field: personal photos are only known by the content id the TV assigns (`MY_F0017`). `SamsungFrameArtworkNames` keeps the names in a `Store` per config entry (`samsung_frame.<entry_id>.artwork_names`), deleted in `async_remove_entry`. `upload_artwork` names the upload (`name` field → `metadata.title` from the media selector → file name via `suggested_artwork_name`), `delete_artwork` forgets the name, and `rename_artwork` calls `coordinator.async_update_listeners()` so the sensor shows the new name without a TV round trip.
- `samsungtvws` is also a requirement of the core `samsungtv` integration, so hassfest rejects an exact pin in `manifest.json`: the manifest declares `samsungtvws>=<version>` and the `dev` group pins that same version with `==`. `tests/test_manifest.py` keeps the two in step; bump both together.
