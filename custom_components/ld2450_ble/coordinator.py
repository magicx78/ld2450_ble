"""Push coordinator for the LD2450 BLE integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HassJob, HomeAssistant, callback
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, UPDATE_DEBOUNCE
from .ld2450_ble import LD2450BLE

_LOGGER = logging.getLogger(__name__)


class LD2450BLECoordinator(DataUpdateCoordinator[None]):
    """Relays push updates from the BLE device to entities.

    The LD2450 pushes data over BLE notifications, so there is no polling. The
    library fires a callback on every decoded frame; we debounce those bursts
    and notify listeners.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        device: LD2450BLE,
    ) -> None:
        """Initialise the coordinator."""
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN)
        self.device = device
        self.connected = False
        self._debounce_cancel: CALLBACK_TYPE | None = None
        self._debounce_job = HassJob(self._async_emit, "ld2450_ble emit")
        device.register_callback(self._handle_update)
        device.register_disconnected_callback(self._handle_disconnect)

    @callback
    def _handle_update(self) -> None:
        """Handle a new state/config update from the device (debounced)."""
        self.connected = True
        if self._debounce_cancel is not None:
            return
        self._debounce_cancel = async_call_later(
            self.hass, UPDATE_DEBOUNCE, self._debounce_job
        )

    @callback
    def _async_emit(self, _now=None) -> None:
        """Flush the debounced update to listeners."""
        self._debounce_cancel = None
        self.async_set_updated_data(None)

    @callback
    def _handle_disconnect(self) -> None:
        """Handle a device disconnect."""
        self.connected = False
        self.async_update_listeners()

    async def async_shutdown(self) -> None:
        """Cancel pending work on shutdown."""
        if self._debounce_cancel is not None:
            self._debounce_cancel()
            self._debounce_cancel = None
        await super().async_shutdown()
