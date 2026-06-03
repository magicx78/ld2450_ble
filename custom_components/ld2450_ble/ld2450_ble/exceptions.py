"""Exceptions for the embedded LD2450 BLE library."""

from __future__ import annotations


class LD2450BLEError(Exception):
    """Base error for the LD2450 BLE library."""


class CharacteristicMissingError(LD2450BLEError):
    """Raised when a required GATT characteristic is missing."""
