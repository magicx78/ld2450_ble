"""Constants for the LD2450 BLE integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "ld2450_ble"

# Advertised local-name prefixes used for discovery filtering.
LOCAL_NAMES: Final = {"HLK-LD2450"}

# Options-flow flag: expose Radar Map Manager-compatible entities (the per-target
# X/Y coordinate sensors enabled, plus a presence_target_count sensor). Opt-in.
CONF_ENABLE_RMM: Final = "enable_radar_map_manager"
DEFAULT_ENABLE_RMM: Final = False

# Debounce window for coalescing rapid push updates (seconds).
UPDATE_DEBOUNCE: Final = 1.0

# Max time (seconds) to wait for the initial connection during setup before
# raising ConfigEntryNotReady. Kept well below Home Assistant's bootstrap stage
# timeout (120 s) so we fail cleanly into a retry instead of being cancelled.
DEVICE_TIMEOUT: Final = 30

# --- Connectivity diagnostics ---------------------------------------------

# No valid data for this long (seconds) while still connected -> "stale".
STALE_TIMEOUT: Final = 30

# Periodic refresh (seconds) so duration/state diagnostics keep ticking while
# the device is idle or offline (no push updates arrive then).
DIAGNOSTIC_REFRESH_INTERVAL: Final = 30

# After a disconnect, report "reconnecting" for this long (seconds) before
# falling back to "disconnected" (the BLE library auto-retries in this window).
RECONNECT_GRACE: Final = 60

# connection_state values.
STATE_CONNECTED: Final = "connected"
STATE_RECONNECTING: Final = "reconnecting"
STATE_DISCONNECTED: Final = "disconnected"
STATE_STALE: Final = "stale"
CONNECTION_STATES: Final = [
    STATE_CONNECTED,
    STATE_RECONNECTING,
    STATE_DISCONNECTED,
    STATE_STALE,
]
