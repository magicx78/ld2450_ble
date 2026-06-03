"""Embedded BLE library for the HLK-LD2450 mmWave radar."""

from __future__ import annotations

from .const import MULTI_TARGET_MODE, SINGLE_TARGET_MODE
from .exceptions import CharacteristicMissingError, LD2450BLEError
from .ld2450_ble import BLEAK_EXCEPTIONS, LD2450BLE
from .models import LD2450BLEConfig, LD2450BLEState, Target

__version__ = "0.1.0"

__all__ = [
    "BLEAK_EXCEPTIONS",
    "CharacteristicMissingError",
    "LD2450BLE",
    "LD2450BLEConfig",
    "LD2450BLEError",
    "LD2450BLEState",
    "MULTI_TARGET_MODE",
    "SINGLE_TARGET_MODE",
    "Target",
]
