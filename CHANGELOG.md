# Changelog

## [1.0.1](https://github.com/roquerodrigo/ha-samsung-frame/compare/v1.0.0...v1.0.1) (2026-11-15)

### Bug fixes

- Home Assistant no longer hangs at startup when the TV's Art Mode service stops answering; requests now give up after their timeout and the entry retries in the background. ([#14](https://github.com/roquerodrigo/ha-samsung-frame/pull/14))
- The integration keeps working when the TV revokes its pairing token, for example after the core Samsung Smart TV integration reconnects; it asks to pair again only if the TV refuses the connection. ([#14](https://github.com/roquerodrigo/ha-samsung-frame/pull/14))
- Pairing works on recent firmware, because the approval request now goes through the channel where the TV still shows the prompt. ([#14](https://github.com/roquerodrigo/ha-samsung-frame/pull/14))
- A firmware update that changes the TV identifier no longer breaks the entry; the TV is recognised by its MAC address and its device and entities keep their history. ([#14](https://github.com/roquerodrigo/ha-samsung-frame/pull/14))
- Reconfiguring the entry no longer reports a different TV after the TV identifier changes. ([#14](https://github.com/roquerodrigo/ha-samsung-frame/pull/14))
- Turning Art Mode on or off when it is already in that state no longer fails. ([#14](https://github.com/roquerodrigo/ha-samsung-frame/pull/14))

## 1.0.0 (2026-10-25)


### Features

* add the Samsung The Frame integration ([02e5b65](https://github.com/roquerodrigo/ha-samsung-frame/commit/02e5b6503f83b2040b92c19376e06fe3784339ed))

## Changelog
