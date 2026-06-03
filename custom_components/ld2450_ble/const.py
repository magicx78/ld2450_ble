"""Constants for the LD2450 BLE integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "ld2450_ble"

# Advertised local-name prefixes used for discovery filtering.
LOCAL_NAMES: Final = {"HLK-LD2450"}

# Debounce window for coalescing rapid push updates (seconds).
UPDATE_DEBOUNCE: Final = 1.0
