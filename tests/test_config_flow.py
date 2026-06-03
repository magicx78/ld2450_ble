"""Tests for the LD2450 BLE config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from bleak import BleakError
from homeassistant.config_entries import SOURCE_BLUETOOTH
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.ld2450_ble.const import DOMAIN

from .conftest import ADDRESS, NAME


@pytest.fixture(autouse=True)
def _bypass_bluetooth_adapters_setup(hass: HomeAssistant) -> None:
    """Treat the ``bluetooth_adapters`` dependency as already set up.

    Loading the config-flow handler makes Home Assistant process the
    integration's dependencies; setting up the real ``bluetooth_adapters``
    integration needs a running D-Bus, which is absent in some environments
    (e.g. WSL). The flow itself only needs its handler loaded, so marking the
    dependency as loaded keeps these tests hermetic.
    """
    hass.config.components.add("bluetooth_adapters")


async def test_bluetooth_discovery_creates_entry(
    hass: HomeAssistant, service_info
) -> None:
    """A discovered device can be confirmed and creates an entry."""
    with patch("custom_components.ld2450_ble.config_flow.LD2450BLE") as mock_device:
        instance = mock_device.return_value
        instance.initialise = AsyncMock()
        instance.stop = AsyncMock()

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=service_info
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_ADDRESS: ADDRESS}
        )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == NAME
    assert result2["data"] == {CONF_ADDRESS: ADDRESS}
    instance.initialise.assert_awaited_once()
    instance.stop.assert_awaited_once()


async def test_bluetooth_discovery_cannot_connect(
    hass: HomeAssistant, service_info
) -> None:
    """A connection failure surfaces a cannot_connect error."""
    with patch("custom_components.ld2450_ble.config_flow.LD2450BLE") as mock_device:
        instance = mock_device.return_value
        instance.initialise = AsyncMock(side_effect=BleakError("boom"))
        instance.stop = AsyncMock()

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=service_info
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_ADDRESS: ADDRESS}
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_bluetooth_discovery_already_configured(
    hass: HomeAssistant, service_info
) -> None:
    """A second discovery of a configured device aborts."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=ADDRESS, data={CONF_ADDRESS: ADDRESS}
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=service_info
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options_flow_toggles_rmm(hass: HomeAssistant) -> None:
    """The options flow stores the Radar Map Manager support toggle."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.ld2450_ble.const import CONF_ENABLE_RMM

    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=ADDRESS, data={CONF_ADDRESS: ADDRESS}
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_ENABLE_RMM: True}
    )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {CONF_ENABLE_RMM: True}
