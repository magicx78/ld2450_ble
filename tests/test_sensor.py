"""Unit tests for the RMM-compatible sensor behaviour.

These exercise the X/Y coordinate sensors and the presence-count sensor without
spinning up Home Assistant, mirroring the lightweight style of ``test_models.py``.
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

ADDRESS = "06:DE:83:53:1B:6F"


def _desc(key: str):
    """Return the sensor description with the given key."""
    return next(d for d in SENSOR_TYPES if d.key == key)


def _state(*targets: Target) -> LD2450BLEState:
    """Build a 3-slot state, padding missing slots with empty targets."""
    slots = list(targets) + [Target() for _ in range(3 - len(targets))]
    return LD2450BLEState(targets=tuple(slots))


def _coordinator(state: LD2450BLEState):
    """A minimal stand-in good enough for the entity constructors."""
    return types.SimpleNamespace(
        device=types.SimpleNamespace(address=ADDRESS, state=state),
        config_entry=types.SimpleNamespace(title="HLK-LD2450"),
    )


def _target_sensor(
    key: str, index: int, state: LD2450BLEState, rmm_enabled: bool = False
) -> LD2450BLESensor:
    return LD2450BLESensor(_coordinator(state), _desc(key), index, rmm_enabled)


def test_xy_none_when_absent_flag() -> None:
    """X/Y are flagged none-when-absent; the other fields are not."""
    assert _desc("x").none_when_absent is True
    assert _desc("y").none_when_absent is True
    assert _desc("distance").none_when_absent is False


def test_xy_unit_is_millimetres() -> None:
    """RMM consumes mm as-is; the unit must stay millimetres."""
    for key in ("x", "y"):
        assert _desc(key).native_unit_of_measurement == UnitOfLength.MILLIMETERS


def test_xy_enabled_follows_rmm_option() -> None:
    """X/Y are enabled by default only when the RMM option is on."""
    st = _state()

    def enabled(key: str, rmm: bool) -> bool:
        sensor = _target_sensor(key, 0, st, rmm_enabled=rmm)
        return sensor.entity_registry_enabled_default

    assert enabled("x", True)
    assert enabled("y", True)
    assert not enabled("x", False)
    assert not enabled("y", False)
    # A non-coordinate sensor ignores the RMM flag (distance stays enabled).
    assert enabled("distance", False)


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
    count = LD2450BLEPresenceCountSensor(
        _coordinator(_state(Target(x=1, y=2, speed=3), Target(x=4, y=5, speed=6)))
    )
    assert count.native_value == 2

    count = LD2450BLEPresenceCountSensor(_coordinator(_state()))
    assert count.native_value == 0

    count = LD2450BLEPresenceCountSensor(
        _coordinator(
            _state(
                Target(x=1, y=1, speed=1),
                Target(x=2, y=2, speed=2),
                Target(x=3, y=3, speed=3),
            )
        )
    )
    assert count.native_value == 3
