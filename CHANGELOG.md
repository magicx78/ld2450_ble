# Changelog

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
