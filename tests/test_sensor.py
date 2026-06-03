"""Unit tests for the RMM-compatible sensor behaviour.

These exercise the pure ``native_value`` logic of the X/Y coordinate sensors
and the presence-count sensor without spinning up Home Assistant, mirroring the
lightweight style of ``test_models.py``.
"""

from __future__ import annotations

import types

from homeassistant.const import UnitOfLength

from custom_components.ld2450_ble.ld2450_ble.models import LD2450BLEState, Target
from custom_components.ld2450_ble.sensor import (
    SENSOR_TYPES,
    LD2450BLEPresenceCountSensor,
    LD2450BLESensor,
)


def _desc(key: str):
    """Return the sensor description with the given key."""
    return next(d for d in SENSOR_TYPES if d.key == key)


def _state(*targets: Target) -> LD2450BLEState:
    """Build a 3-slot state, padding missing slots with empty targets."""
    slots = list(targets) + [Target() for _ in range(3 - len(targets))]
    return LD2450BLEState(targets=tuple(slots))


def _fake_coordinator(state: LD2450BLEState):
    """A minimal stand-in exposing ``coordinator.device.state``."""
    return types.SimpleNamespace(device=types.SimpleNamespace(state=state))


def _target_sensor(key: str, index: int, state: LD2450BLEState) -> LD2450BLESensor:
    """Build an LD2450BLESensor without the HA entity machinery."""
    sensor = LD2450BLESensor.__new__(LD2450BLESensor)
    sensor.entity_description = _desc(key)
    sensor._index = index
    sensor.coordinator = _fake_coordinator(state)
    return sensor


def test_xy_enabled_by_default() -> None:
    """X/Y must be enabled by default and flagged none-when-absent for RMM."""
    for key in ("x", "y"):
        desc = _desc(key)
        assert desc.entity_registry_enabled_default is not False
        assert desc.none_when_absent is True


def test_xy_unit_is_millimetres() -> None:
    """RMM consumes mm as-is; the unit must stay millimetres."""
    for key in ("x", "y"):
        assert _desc(key).native_unit_of_measurement == UnitOfLength.MILLIMETERS


def test_xy_present_returns_coordinate() -> None:
    """A present target reports its raw mm coordinates."""
    state = _state(Target(x=-782, y=1100, speed=-236))
    assert _target_sensor("x", 0, state).native_value == -782
    assert _target_sensor("y", 0, state).native_value == 1100


def test_xy_absent_returns_none() -> None:
    """Empty slots report unknown (None) so RMM skips them cleanly."""
    state = _state(Target(x=-782, y=1100, speed=-236))
    assert _target_sensor("x", 1, state).native_value is None
    assert _target_sensor("y", 2, state).native_value is None


def test_presence_target_count() -> None:
    """The count reflects how many slots hold a real detection (0..3)."""
    count = LD2450BLEPresenceCountSensor.__new__(LD2450BLEPresenceCountSensor)

    count.coordinator = _fake_coordinator(
        _state(Target(x=1, y=2, speed=3), Target(x=4, y=5, speed=6))
    )
    assert count.native_value == 2

    count.coordinator = _fake_coordinator(_state())
    assert count.native_value == 0

    count.coordinator = _fake_coordinator(
        _state(
            Target(x=1, y=1, speed=1),
            Target(x=2, y=2, speed=2),
            Target(x=3, y=3, speed=3),
        )
    )
    assert count.native_value == 3
