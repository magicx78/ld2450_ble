"""The LD2450 BLE integration."""

from __future__ import annotations

import logging

from bleak_retry_connector import close_stale_connections_by_address, get_device
from homeassistant.components import bluetooth
from homeassistant.components.bluetooth.match import ADDRESS, BluetoothCallbackMatcher
from homeassistant.const import CONF_ADDRESS, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .coordinator import LD2450BLECoordinator
from .ld2450_ble import BLEAK_EXCEPTIONS, LD2450BLE
from .models import LD2450BLEConfigEntry, LD2450BLEData

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: LD2450BLEConfigEntry) -> bool:
    """Set up LD2450 BLE from a config entry."""
    address: str = entry.data[CONF_ADDRESS]
    await close_stale_connections_by_address(address)

    ble_device = bluetooth.async_ble_device_from_address(
        hass, address.upper(), True
    ) or await get_device(address)
    if not ble_device:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="device_not_found",
            translation_placeholders={"address": address},
        )

    device = LD2450BLE(ble_device)
    coordinator = LD2450BLECoordinator(hass, entry, device)

    try:
        await device.initialise()
    except BLEAK_EXCEPTIONS as exc:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="cannot_connect",
            translation_placeholders={"address": address},
        ) from exc

    @callback
    def _async_update_ble(
        service_info: bluetooth.BluetoothServiceInfoBleak,
        change: bluetooth.BluetoothChange,
    ) -> None:
        """Update the BLE device/advertisement from the bluetooth manager."""
        device.set_ble_device_and_advertisement_data(
            service_info.device, service_info.advertisement
        )

    entry.async_on_unload(
        bluetooth.async_register_callback(
            hass,
            _async_update_ble,
            BluetoothCallbackMatcher({ADDRESS: address}),
            bluetooth.BluetoothScanningMode.ACTIVE,
        )
    )

    async def _async_stop(event: Event | None = None) -> None:
        await device.stop()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_stop)
    )

    # Start periodic diagnostic refresh and ensure its timers are cancelled
    # when the entry is unloaded.
    coordinator.async_start()
    entry.async_on_unload(coordinator.async_shutdown)

    entry.runtime_data = LD2450BLEData(entry.title, device, coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def _async_options_updated(
    hass: HomeAssistant, entry: LD2450BLEConfigEntry
) -> None:
    """Reload the entry when its options change (e.g. RMM support toggled)."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: LD2450BLEConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.device.stop()
    return unload_ok
