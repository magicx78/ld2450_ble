"""Tests for the LD2450 BLE integration setup."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from custom_components.ld2450_ble import async_setup_entry
from custom_components.ld2450_ble.const import DOMAIN

from .conftest import ADDRESS


async def test_setup_entry_device_not_found(hass: HomeAssistant) -> None:
    """Setup raises ConfigEntryNotReady when the device cannot be located."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=ADDRESS, data={CONF_ADDRESS: ADDRESS}
    )
    entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.ld2450_ble.close_stale_connections_by_address",
            AsyncMock(),
        ),
        patch(
            "homeassistant.components.bluetooth.async_ble_device_from_address",
            return_value=None,
        ),
        patch(
            "custom_components.ld2450_ble.get_device",
            AsyncMock(return_value=None),
        ),
        pytest.raises(ConfigEntryNotReady),
    ):
        await async_setup_entry(hass, entry)
