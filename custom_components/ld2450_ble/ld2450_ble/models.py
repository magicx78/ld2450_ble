"""Data models and frame parsing for the embedded LD2450 BLE library."""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

from .const import FRAME_HEADER, FRAME_LENGTH, FRAME_TAIL, TARGET_COUNT, TARGET_SIZE


@dataclass(frozen=True)
class Target:
    """A single tracked target."""

    x: int = 0  # mm, lateral (+/-)
    y: int = 0  # mm, forward distance from sensor
    speed: int = 0  # cm/s (negative = approaching)
    resolution: int = 0  # mm, distance resolution gate

    @property
    def present(self) -> bool:
        """Return True if this target slot holds a real detection.

        An empty slot is reported as all-zero bytes.
        """
        return not (self.x == 0 and self.y == 0 and self.speed == 0)

    @property
    def moving(self) -> bool:
        """Return True if the target is moving."""
        return self.speed != 0

    @property
    def distance(self) -> float:
        """Euclidean distance from the sensor in mm."""
        return math.hypot(self.x, self.y)

    @property
    def angle(self) -> float:
        """Bearing in degrees (0 = straight ahead, +/- to the sides)."""
        return math.degrees(math.atan2(self.x, self.y))


@dataclass(frozen=True)
class LD2450BLEState:
    """Decoded cyclic target state."""

    targets: tuple[Target, ...] = field(
        default_factory=lambda: tuple(Target() for _ in range(TARGET_COUNT))
    )

    @property
    def any_present(self) -> bool:
        """Return True if any target is present."""
        return any(t.present for t in self.targets)


@dataclass(frozen=True)
class LD2450BLEConfig:
    """Decoded device configuration / metadata."""

    target_mode: int = 0
    fw_ver: str = ""
    mac_addr: str = ""
    area_mode: int = 0
    # 3 areas, each defined by two vertices (x1, y1, x2, y2) -> 12 values.
    area_vertices: tuple[int, ...] = field(default_factory=lambda: tuple([0] * 12))


def _decode_signed(low: int, high: int) -> int:
    """Decode an LD2450 16-bit sign-magnitude little-endian value.

    The LD2450 does NOT use two's complement. Bit 15 is a sign flag where
    1 means POSITIVE and 0 means NEGATIVE; the low 15 bits are the magnitude.

    Official HLK example: bytes ``0E 03`` -> magnitude 782, bit15 (of 0x03) is
    0 -> ``-782``.
    """
    magnitude = ((high & 0x7F) << 8) | low
    return magnitude if (high & 0x80) else -magnitude


def parse_target_frame(frame: bytes) -> LD2450BLEState | None:
    """Parse a 30-byte target-data frame into an :class:`LD2450BLEState`.

    Returns ``None`` if the frame does not have the expected header/tail/length.
    """
    if (
        len(frame) != FRAME_LENGTH
        or not frame.startswith(FRAME_HEADER)
        or not frame.endswith(FRAME_TAIL)
    ):
        return None

    targets: list[Target] = []
    for i in range(TARGET_COUNT):
        base = len(FRAME_HEADER) + i * TARGET_SIZE
        block = frame[base : base + TARGET_SIZE]
        x = _decode_signed(block[0], block[1])
        y = _decode_signed(block[2], block[3])
        speed = _decode_signed(block[4], block[5])
        resolution = block[6] | (block[7] << 8)  # unsigned, little-endian
        targets.append(Target(x=x, y=y, speed=speed, resolution=resolution))

    return LD2450BLEState(targets=tuple(targets))


def with_area_vertex(
    config: LD2450BLEConfig, index: int, value: int
) -> LD2450BLEConfig:
    """Return a copy of ``config`` with a single area vertex value replaced."""
    vertices = list(config.area_vertices)
    vertices[index] = value
    return replace(config, area_vertices=tuple(vertices))
