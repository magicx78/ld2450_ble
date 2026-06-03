"""Shared fixtures for the LD2450 BLE tests."""

from __future__ import annotations

import pytest
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak

pytest_plugins = ["pytest_homeassistant_custom_component"]

ADDRESS = "06:DE:83:53:1B:6F"
NAME = "HLK-LD2450_1B6F"
SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading of the custom integration in every test."""
    yield


def make_ble_device(address: str = ADDRESS, name: str = NAME) -> BLEDevice:
    """Build a BLEDevice for the pinned bleak 3.x signature."""
    return BLEDevice(address, name, {})


def make_advertisement(name: str = NAME) -> AdvertisementData:
    """Build AdvertisementData for the pinned bleak 3.x signature."""
    return AdvertisementData(
        local_name=name,
        manufacturer_data={},
        service_data={},
        service_uuids=[SERVICE_UUID],
        tx_power=-127,
        rssi=-60,
        platform_data=(),
    )


def make_service_info(
    address: str = ADDRESS, name: str = NAME
) -> BluetoothServiceInfoBleak:
    """Build a BluetoothServiceInfoBleak fixture."""
    return BluetoothServiceInfoBleak(
        name=name,
        address=address,
        rssi=-60,
        manufacturer_data={},
        service_uuids=[SERVICE_UUID],
        service_data={},
        source="local",
        device=make_ble_device(address, name),
        advertisement=make_advertisement(name),
        connectable=True,
        time=0,
        tx_power=-127,
    )


@pytest.fixture
def service_info() -> BluetoothServiceInfoBleak:
    """Return a discovery service info for the LD2450."""
    return make_service_info()
