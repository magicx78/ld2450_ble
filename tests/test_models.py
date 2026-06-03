"""Unit tests for the LD2450 frame parser (no Home Assistant required)."""

from __future__ import annotations

import math

import pytest

from custom_components.ld2450_ble.ld2450_ble.models import (
    Target,
    parse_target_frame,
)

# Verified test vector. T1 = X=-782, Y=+1100, speed=-236 cm/s, resolution=100.
#   X bytes 0E 03 -> mag 782, bit15(0x03)=0 -> -782   (official HLK example)
#   Y bytes 4C 84 -> mag 0x044C=1100, bit15(0x84)=1 -> +1100
#   V bytes EC 00 -> mag 236, bit15(0x00)=0 -> -236
#   res bytes 64 00 -> 100 (unsigned)
FRAME_ONE_TARGET = bytes.fromhex(
    "AAFF03000E034C84EC0064000000000000000000000000000000000055CC"
)


def test_parse_single_target() -> None:
    """Decode a frame with one real target and two empty slots."""
    state = parse_target_frame(FRAME_ONE_TARGET)
    assert state is not None

    t1 = state.targets[0]
    assert t1.x == -782
    assert t1.y == 1100
    assert t1.speed == -236
    assert t1.resolution == 100
    assert t1.present is True
    assert t1.moving is True
    assert t1.distance == pytest.approx(math.hypot(-782, 1100))
    assert t1.angle == pytest.approx(math.degrees(math.atan2(-782, 1100)))

    assert state.targets[1].present is False
    assert state.targets[2].present is False
    assert state.any_present is True


def test_positive_x_sign_bit() -> None:
    """Bit15 set means a positive coordinate (sign-magnitude, inverted bit)."""
    # T1 block: X bytes 0E 83 -> mag 782, bit15(0x83)=1 -> +782; rest zero.
    frame = bytes.fromhex(
        "AAFF0300"
        "0E83000000000000"  # T1 (8 bytes)
        "0000000000000000"  # T2
        "0000000000000000"  # T3
        "55CC"
    )
    state = parse_target_frame(frame)
    assert state is not None
    assert state.targets[0].x == 782


def test_empty_frame_no_presence() -> None:
    """An all-zero target payload reports no presence."""
    frame = bytes.fromhex("AAFF0300" + "00" * 24 + "55CC")
    state = parse_target_frame(frame)
    assert state is not None
    assert state.any_present is False
    assert all(not t.present for t in state.targets)


@pytest.mark.parametrize(
    "frame",
    [
        b"",
        b"\x00" * 30,  # wrong header
        bytes.fromhex("AAFF0300" + "00" * 24 + "0000"),  # wrong tail
        bytes.fromhex("AAFF0300" + "00" * 10 + "55CC"),  # too short
    ],
)
def test_parse_rejects_invalid(frame: bytes) -> None:
    """Malformed frames return None instead of raising."""
    assert parse_target_frame(frame) is None


def test_target_defaults() -> None:
    """A default Target is absent and stationary."""
    t = Target()
    assert t.present is False
    assert t.moving is False
    assert t.distance == 0
