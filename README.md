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

> Verified end-to-end on real HLK-LD2450 hardware with Home Assistant 2026.2.3
> (discovery, connection, live data, all entities).

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
| `sensor` | Target N X / Y | mm — enabled when *Radar Map Manager support* is on; unknown when the slot is empty |
| `sensor` | Presence target count | 0–3 currently present targets; only created when *Radar Map Manager support* is on |
| `sensor` | Target N speed | mm/s, disabled by default |
| `sensor` | Target N resolution | mm, disabled by default |
| `switch` | Multi-target tracking | On = multi, off = single |
| `select` | Area mode | Disabled / Monitor / Ignore |
| `number` | Area N vertex M X/Y | 12 area-filter sliders, disabled by default |
| `button` | Reboot | Restarts the sensor module |

> The area-filter writes (select + number) are best-effort against the documented
> command and should be confirmed on your hardware.

## Diagnostic sensors

Each device also exposes connectivity **diagnostics** (entity category
*diagnostic*, created automatically — no YAML), so you can tell whether the
sensor is reliably online or keeps dropping:

| Entity | Type | Meaning |
|---|---|---|
| `binary_sensor.<device>_ble_connected` | connectivity | On = connected with fresh data |
| `sensor.<device>_connection_state` | enum | `connected` / `reconnecting` / `disconnected` / `stale` |
| `sensor.<device>_last_seen` | timestamp | Last valid BLE packet received |
| `sensor.<device>_last_disconnect` | timestamp | Last detected interruption |
| `sensor.<device>_disconnect_count` | count | Interruptions since start/reload (once per interruption) |
| `sensor.<device>_reconnect_count` | count | Successful reconnections since start/reload |
| `sensor.<device>_offline_duration` | seconds | Current (or last) offline phase |
| `sensor.<device>_online_duration` | seconds | Current online phase |

State logic lives centrally in the coordinator. A connection that stays up but
delivers no data for `STALE_TIMEOUT` (30 s) is reported as **stale**; after a
drop the state is **reconnecting** while the library retries, then
**disconnected**.

> **TODO:** `sensor.<device>_reliability_24h` (24 h online percentage) is not
> implemented yet — a correct version needs persistent 24 h history
> (recorder/restore) rather than an in-memory value that resets on restart.

## Radar Map Manager (RMM) support

This integration is compatible with
[Moe8383/radar_map_manager](https://github.com/Moe8383/radar_map_manager), which
visualises radar targets on a floor-plan map.

RMM reads each radar purely by **entity-id convention**:

```
sensor.<radar>_target_1_x
sensor.<radar>_target_1_y
sensor.<radar>_target_2_x
sensor.<radar>_target_2_y
sensor.<radar>_target_3_x
sensor.<radar>_target_3_y
```

The `Target N X / Y` sensors provide exactly these — in **millimetres**, which RMM
uses as-is (it reads `unit_of_measurement`; `m` and `cm` are scaled, `mm` is taken
directly). An empty target slot reports `unknown`, which RMM skips cleanly. No
helper templates or duplicate sensors are required.

### Turn it on (opt-in)

RMM support is **off by default** so non-RMM users keep a clean entity list. To
enable it, go to **Settings → Devices & Services → LD2450 BLE → Configure** and
turn on **Radar Map Manager support**. The integration reloads and:

- enables the six `Target N X / Y` sensors, and
- adds a `presence_target_count` sensor (0–3).

Turning the option back off disables them again.

### Matching the radar name (and a language caveat)

RMM looks up the literal entity-ids `sensor.<radar>_target_<n>_x` / `_y`, where
`<radar>` is the name you pass to RMM. Home Assistant generates an entity-id from
the device name **and the entity name in your configured language**, so both
parts must line up:

- **Prefix** = the device-name slug (e.g. device `HLK-LD2450 1B6F` →
  `sensor.hlk_ld2450_1b6f_…`).
- **Suffix** = `target_<n>_x`. This is the English entity name. **If your Home
  Assistant runs in another language the suffix is translated** — e.g. in German
  it becomes `…_ziel_1_x`, which RMM will *not* find.

So for RMM, make sure the X/Y entity-ids end in `_target_<n>_x` / `_y`:

- **English HA:** already correct out of the box — just give the device a clean
  name (e.g. `rd_ld2450`).
- **Non-English HA:** rename the six X/Y **entity-ids** (not just the device) to
  the `target_<n>` form under **Settings → Devices & Services → LD2450 BLE →
  device → the entity → ⚙ → Entity ID**.

Either way the target entity-ids become:

```
sensor.rd_ld2450_target_1_x
sensor.rd_ld2450_target_1_y
sensor.rd_ld2450_presence_target_count
```

### Registering in RMM

Call the RMM service with the matching name:

```yaml
service: radar_map_manager.add_radar
data:
  radar_name: rd_ld2450
  map_group: default
```

> `presence_target_count` (0–3) is provided as a convenience and for dashboards.
> RMM computes its own fused target count across radars
> (`sensor.rmm_<map>_master`), so it does not consume this sensor directly.

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
