# Changelog

## [0.2.0] - Unreleased
### Added
- Connectivity **diagnostic** entities, created automatically per device
  (no YAML), in the diagnostic category:
  - `binary_sensor.<device>_ble_connected` (device_class `connectivity`)
  - `sensor.<device>_last_seen` (timestamp)
  - `sensor.<device>_connection_state` (enum: connected / reconnecting /
    disconnected / stale)
  - `sensor.<device>_disconnect_count`
  - `sensor.<device>_reconnect_count`
  - `sensor.<device>_last_disconnect` (timestamp)
  - `sensor.<device>_offline_duration` (seconds)
  - `sensor.<device>_online_duration` (seconds)
- Central connectivity state tracking in the coordinator with a stale watchdog
  (`STALE_TIMEOUT`, 30 s) and a periodic refresh so durations keep ticking
  while offline.
- `LD2450BLE.is_connected` property (BLE library).

### Notes
- `sensor.<device>_reliability_24h` is intentionally **not** implemented yet:
  doing it correctly needs persistent 24 h history (recorder/restore). Tracked
  as a TODO rather than shipping an in-memory approximation that resets on
  restart.

## [0.1.1] - 2026-06-03
### Changed
- Production-grade README (CI badges, entities table, development section).
- GitHub repository description and topics.

### Verified
- End-to-end on **real hardware** (HLK-LD2450 over BLE, Home Assistant 2026.2.3):
  discovery, GATT connection, live ~1 Hz data, and all 40 entities across the six
  platforms. No code changes were required — the 0.1.0 logic worked as-is.

## [0.1.0] - 2026-06-03
### Added
- Initial release: native BLE integration for the HLK-LD2450 mmWave radar.
- Bluetooth auto-discovery config flow (works through ESPHome Bluetooth proxies).
- Push coordinator with up to 3 targets.
- Sensors: per-target distance, angle, X, Y, speed, resolution.
- Binary sensors: aggregate presence, per-target present/moving.
- Config controls: multi-/single-target switch, area-mode select, 12 area-vertex
  number sliders, reboot button.
- Corrected LD2450 sign-magnitude coordinate decoding (inverted sign bit).
- Tests (parser, config flow, setup) and CI (hassfest, HACS, ruff, pytest).
