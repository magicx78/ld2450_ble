"""Runtime data models for the LD2450 BLE integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry

from .coordinator import LD2450BLECoordinator
from .ld2450_ble import LD2450BLE

type LD2450BLEConfigEntry = ConfigEntry[LD2450BLEData]


@dataclass
class LD2450BLEData:
    """Per-entry runtime data for the LD2450 BLE integration."""

    title: str
    device: LD2450BLE
    coordinator: LD2450BLECoordinator
