"""Tests for the connectivity diagnostics state machine in the coordinator."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ld2450_ble.const import (
    DOMAIN,
    RECONNECT_GRACE,
    STALE_TIMEOUT,
    STATE_CONNECTED,
    STATE_DISCONNECTED,
    STATE_RECONNECTING,
    STATE_STALE,
)
from custom_components.ld2450_ble.coordinator import LD2450BLECoordinator

from .conftest import ADDRESS, NAME


@pytest.fixture
def mock_device() -> MagicMock:
    """A mock BLE device with a controllable is_connected flag."""
    device = MagicMock()
    device.address = ADDRESS
    device.name = NAME
    device.is_connected = True
    return device


@pytest.fixture
async def coordinator(hass: HomeAssistant, mock_device: MagicMock):
    """A coordinator wired to the mock device (timers cancelled on teardown)."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=ADDRESS, data={"address": ADDRESS})
    entry.add_to_hass(hass)
    coord = LD2450BLECoordinator(hass, entry, mock_device)
    yield coord
    await coord.async_shutdown()


async def test_initial_connected_state(coordinator: LD2450BLECoordinator) -> None:
    """First data packet puts the device into the connected state."""
    coordinator._handle_update()
    assert coordinator.connection_state == STATE_CONNECTED
    assert coordinator.ble_connected is True
    assert coordinator.last_seen is not None
    assert coordinator.disconnect_count == 0
    assert coordinator.reconnect_count == 0


async def test_last_seen_updates_on_data(coordinator: LD2450BLECoordinator) -> None:
    """last_seen advances with each received packet."""
    coordinator._handle_update()
    first = coordinator.last_seen
    assert first is not None
    coordinator._handle_update()
    assert coordinator.last_seen is not None
    assert coordinator.last_seen >= first


async def test_disconnect_count_once_per_interruption(
    coordinator: LD2450BLECoordinator,
) -> None:
    """disconnect_count increments once per interruption, not per callback."""
    coordinator._handle_update()  # online
    coordinator._handle_disconnect()  # first drop -> count 1
    coordinator._handle_disconnect()  # still offline -> no extra count
    assert coordinator.disconnect_count == 1
    assert coordinator.last_disconnect is not None


async def test_reconnect_count_increments_on_recovery(
    coordinator: LD2450BLECoordinator,
) -> None:
    """reconnect_count increments only on a successful reconnection."""
    coordinator._handle_update()  # initial connect (not a reconnect)
    assert coordinator.reconnect_count == 0
    coordinator._handle_disconnect()
    coordinator._handle_update()  # recovered -> reconnect 1
    assert coordinator.reconnect_count == 1
    assert coordinator.connection_state == STATE_CONNECTED


async def test_stale_state_after_timeout(
    coordinator: LD2450BLECoordinator, mock_device: MagicMock
) -> None:
    """Connected but no fresh data for STALE_TIMEOUT -> stale."""
    coordinator._handle_update()
    mock_device.is_connected = True
    coordinator.last_seen = dt_util.utcnow() - timedelta(seconds=STALE_TIMEOUT + 5)
    assert coordinator.connection_state == STATE_STALE
    assert coordinator.ble_connected is False


async def test_reconnecting_then_disconnected(
    coordinator: LD2450BLECoordinator, mock_device: MagicMock
) -> None:
    """After a drop: reconnecting within grace, then disconnected."""
    coordinator._handle_update()
    coordinator._handle_disconnect()
    mock_device.is_connected = False
    assert coordinator.connection_state == STATE_RECONNECTING
    # Simulate the grace window having elapsed.
    coordinator._offline_since = dt_util.utcnow() - timedelta(
        seconds=RECONNECT_GRACE + 5
    )
    assert coordinator.connection_state == STATE_DISCONNECTED


async def test_durations(
    coordinator: LD2450BLECoordinator, mock_device: MagicMock
) -> None:
    """Online/offline durations reflect the current phase."""
    coordinator._handle_update()
    mock_device.is_connected = True
    coordinator._online_since = dt_util.utcnow() - timedelta(seconds=12)
    assert coordinator.online_duration >= 12
    assert coordinator.offline_duration == 0

    coordinator._handle_disconnect()
    mock_device.is_connected = False
    coordinator._offline_since = dt_util.utcnow() - timedelta(seconds=7)
    assert coordinator.offline_duration >= 7
    assert coordinator.online_duration == 0
