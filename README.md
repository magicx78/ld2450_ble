# LD2450 BLE for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/magicx78/ld2450_ble.svg)](https://github.com/magicx78/ld2450_ble/releases)
[![Tests](https://github.com/magicx78/ld2450_ble/actions/workflows/tests.yaml/badge.svg)](https://github.com/magicx78/ld2450_ble/actions/workflows/tests.yaml)
[![hassfest](https://github.com/magicx78/ld2450_ble/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/magicx78/ld2450_ble/actions/workflows/hassfest.yaml)
[![HACS](https://github.com/magicx78/ld2450_ble/actions/workflows/hacs.yaml/badge.svg)](https://github.com/magicx78/ld2450_ble/actions/workflows/hacs.yaml)

A native Bluetooth Low Energy integration for the **HiLink HLK-LD2450** 24 GHz
mmWave tracking radar. It connects directly over BLE — including through an
**ESPHome Bluetooth proxy** — and exposes per-target position, presence and
movement, plus configuration controls.

This is a clean, modern rebuild against current Home Assistant, `bleak` 3.x and
`bleak-retry-connector` 4.x APIs (`runtime_data`, push coordinator, corrected
LD2450 sign-magnitude coordinate decoding).

## Features

- Tracks up to **3 targets** simultaneously, pushed in real time (no polling).
- Works locally over BLE, including behind an **ESPHome Bluetooth proxy**.
- Auto-discovery config flow — no YAML needed.
- Per-target position (distance + angle), presence and movement.
- Device configuration from the UI (tracking mode, area filter, reboot).

## Entities

Created per device (target `N` = 1–3):

| Platform | Entity | Notes |
|---|---|---|
| `binary_sensor` | Presence | On if any target is detected |
| `binary_sensor` | Target N present | Occupancy per target |
| `binary_sensor` | Target N moving | Movement per target |
| `sensor` | Target N distance | mm, enabled by default |
| `sensor` | Target N angle | °, enabled by default |
| `sensor` | Target N X / Y | mm, disabled by default |
| `sensor` | Target N speed | mm/s, disabled by default |
| `sensor` | Target N resolution | mm, disabled by default |
| `switch` | Multi-target tracking | On = multi, off = single |
| `select` | Area mode | Disabled / Monitor / Ignore |
| `number` | Area N vertex M X/Y | 12 area-filter sliders, disabled by default |
| `button` | Reboot | Restarts the sensor module |

> The area-filter writes (select + number) are best-effort against the documented
> command and should be confirmed on your hardware.

## Installation

### HACS (custom repository)

1. In Home Assistant open **HACS → ⋮ → Custom repositories**.
2. Add `https://github.com/magicx78/ld2450_ble` with category **Integration**.
3. Search for **LD2450 BLE**, **Download**, then **restart Home Assistant**.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=magicx78&repository=ld2450_ble&category=integration)

### Manual

Copy `custom_components/ld2450_ble/` into your Home Assistant
`config/custom_components/` directory and restart.

## Setup

The sensor is discovered automatically (local name `HLK-LD2450_*`). Make sure a
Bluetooth adapter or an **ESPHome Bluetooth proxy** is in range of the device,
then confirm the discovery card — or go to **Settings → Devices & Services → Add
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

If setup fails, confirm your Bluetooth proxy actually sees the device, then open
an [issue](https://github.com/magicx78/ld2450_ble/issues) with the log excerpt.

## Development

```bash
pip install -r requirements-test.txt
ruff check . && ruff format --check .
pytest tests/ -v
```

CI runs ruff, pytest, `hassfest` and the HACS validator on every push.

## Credits

Protocol and structure inspired by the upstream `MassiPi/ld2450_ble` and the
canonical `ld2410_ble` integration in Home Assistant core.

## License

[MIT](LICENSE)
