# Contributing

Bug reports, ideas and pull requests are welcome.

## Reporting a bug

Open an [issue](https://github.com/roquerodrigo/ha-samsung-frame/issues/new/choose)
with:

- the Home Assistant version, the integration version and the TV model;
- what you did, what you expected and what happened;
- the diagnostics downloaded from the integration's menu (the pairing token
  and the MAC address are redacted) and the relevant log lines.

Debug logs of the `samsungtvws` library contain the pairing token. Remove it
before you attach a log.

## Development setup

The project uses [uv](https://docs.astral.sh/uv/) and Python 3.14.

```bash
scripts/setup      # install the dependencies into .venv
scripts/develop    # run Home Assistant at http://localhost:8123 with this integration loaded
```

`scripts/develop` uses the configuration in [`config/`](config/), which turns
on debug logging for the integration.

## Checks

Run these before opening a pull request. CI runs the same ones, and
`pre-commit install` runs the first three on every commit.

```bash
uv run ruff format .                           # format
uv run ruff check . --fix                      # lint
uv run mypy custom_components/samsung_frame    # type-check
uv run pytest                                  # tests, coverage must stay at 90 % or more
```

`scripts/lint` runs the same checks without changing any file.

Read [CODE_STYLE.md](CODE_STYLE.md) before adding or restructuring code.

## Pull requests

1. Fork the repository and branch from `main`.
2. Write commit messages as [Conventional Commits](https://www.conventionalcommits.org/).
   Releases and their notes are generated from them. Mark breaking changes
   with `!` or a `BREAKING CHANGE:` footer.
3. Update `translations/en.json` and `translations/pt-BR.json` together when
   you change user-facing strings, including the action fields declared in
   `services.yaml`. The tests fail when the two files have different keys.
4. Update the README when behaviour, configuration, entities or actions
   change.
5. Fill in the pull request template.

## License

Contributions are released under the project's [MIT License](LICENSE).
