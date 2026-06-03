"""Constants for the embedded LD2450 BLE library."""

from __future__ import annotations

# GATT characteristics exposed by the HLK-LD2450 BLE module.
CHARACTERISTIC_NOTIFY = "0000fff1-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_WRITE = "0000fff2-0000-1000-8000-00805f9b34fb"

# Cyclic target-data frame (pushed by the sensor, ~10 Hz).
FRAME_HEADER = b"\xaa\xff\x03\x00"
FRAME_TAIL = b"\x55\xcc"
FRAME_LENGTH = 30  # 4 header + 3 * 8 target + 2 tail
TARGET_COUNT = 3
TARGET_SIZE = 8

# Command-frame framing: HEADER + len(LE, 2) + cmd(LE, 2) + value + TAIL.
CMD_HEADER = b"\xfd\xfc\xfb\xfa"
CMD_TAIL = b"\x04\x03\x02\x01"

# Ready-to-send command frames.
CMD_ENABLE_CONFIG = b"\xfd\xfc\xfb\xfa\x04\x00\xff\x00\x01\x00\x04\x03\x02\x01"
CMD_END_CONFIG = b"\xfd\xfc\xfb\xfa\x02\x00\xfe\x00\x04\x03\x02\x01"
CMD_SINGLE_TARGET = b"\xfd\xfc\xfb\xfa\x02\x00\x80\x00\x04\x03\x02\x01"
CMD_MULTI_TARGET = b"\xfd\xfc\xfb\xfa\x02\x00\x90\x00\x04\x03\x02\x01"
CMD_QUERY_TARGET_MODE = b"\xfd\xfc\xfb\xfa\x02\x00\x91\x00\x04\x03\x02\x01"
CMD_RESTART = b"\xfd\xfc\xfb\xfa\x02\x00\xa3\x00\x04\x03\x02\x01"
CMD_BLUETOOTH_ON = b"\xfd\xfc\xfb\xfa\x04\x00\xa4\x00\x01\x00\x04\x03\x02\x01"
CMD_BLUETOOTH_OFF = b"\xfd\xfc\xfb\xfa\x04\x00\xa4\x00\x00\x00\x04\x03\x02\x01"

# Target-tracking modes (sensor convention: 1 = single, 2 = multi).
SINGLE_TARGET_MODE = 1
MULTI_TARGET_MODE = 2

# Area-filter modes.
AREA_DISABLED = 0
AREA_MONITOR = 1
AREA_IGNORE = 2

# Reconnect / timing.
DEFAULT_ATTEMPTS = 3
DISCONNECT_DELAY = 120
