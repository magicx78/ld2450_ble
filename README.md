# LD2450 BLE for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/magicx78/ld2450_ble.svg)](https://github.com/magicx78/ld2450_ble/releases)

A native Bluetooth Low Energy integration for the **HiLink HLK-LD2450** 24 GHz
mmWave tracking radar. It connects directly over BLE — including through an
**ESPHome Bluetooth proxy** — and exposes per-target position, presence and
movement, plus configuration controls.

This is a clean, modern rebuild against current Home Assistant, `bleak` 3.x and
`bleak-retry-connector` 4.x APIs (`runtime_data`, push coordinator, corrected
sign-magnitude coordinate decoding).

## Features

- Up to **3 tracked targets**, each with:
  - Distance (mm) and angle (°) sensors (enabled by default)
  - Raw X / Y / speed / resolution sensors (disabled by default)
  - `present` and `moving` binary sensors
- Aggregate **Presence** binary sensor
- Configuration controls:
  - Multi-/single-target tracking switch
  - Area-filter mode select + 12 area-vertex number sliders *(best-effort; verify
    on your hardware)*
  - Reboot button

## Installation

### HACS (custom repository)

1. In Home Assistant open **HACS → Integrations → ⋮ → Custom repositories**.
2. Add `https://github.com/magicx78/ld2450_ble` with category **Integration**.
3. Search for **LD2450 BLE**, download it, and **restart Home Assistant**.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=magicx78&repository=ld2450_ble&category=integration)

### Manual

Copy `custom_components/ld2450_ble/` into your Home Assistant `config/custom_components/`
directory and restart.

## Setup

The sensor is discovered automatically (local name `HLK-LD2450_*`). Make sure a
Bluetooth adapter or an **ESPHome Bluetooth proxy** is in range of the device,
then confirm the discovery card, or go to **Settings → Devices & Services → Add
Integration → LD2450 BLE**.

## Supported devices

- HiLink HLK-LD2450 (BLE firmware advertising as `HLK-LD2450_*`)

## Troubleshooting

Enable debug logging and capture the log around setup:

```yaml
logger:
  default: info
  logs:
    custom_components.ld2450_ble: debug
```

If setup fails, confirm your Bluetooth proxy (e.g. `keypad-frontdoor`) actually
sees the device, then open an issue with the log excerpt.

## Credits

Protocol and structure inspired by the upstream `MassiPi/ld2450_ble` and the
canonical `ld2410_ble` integration in Home Assistant core.

## License

[MIT](LICENSE)
