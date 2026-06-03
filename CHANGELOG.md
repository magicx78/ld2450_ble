# Changelog

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
