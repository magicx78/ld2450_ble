"""Push coordinator for the LD2450 BLE integration.

Besides relaying the device's push updates to entities, this coordinator is the
single source of truth for connectivity diagnostics (last seen, connection
state, disconnect/reconnect counts, online/offline durations). All state
tracking lives here so the diagnostic entities stay thin.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HassJob, HomeAssistant, callback
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    DIAGNOSTIC_REFRESH_INTERVAL,
    DOMAIN,
    RECONNECT_GRACE,
    STALE_TIMEOUT,
    STATE_CONNECTED,
    STATE_DISCONNECTED,
    STATE_RECONNECTING,
    STATE_STALE,
    UPDATE_DEBOUNCE,
)
from .ld2450_ble import LD2450BLE

_LOGGER = logging.getLogger(__name__)


class LD2450BLECoordinator(DataUpdateCoordinator[None]):
    """Relays push updates and tracks connectivity diagnostics.

    The LD2450 pushes data over BLE notifications, so there is no polling. The
    library fires a callback on every decoded frame; we debounce those bursts
    and notify listeners. Connection events feed a small state machine used by
    the diagnostic entities.
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
        # Backwards-compatible "fresh data" flag used by the regular entities.
        self.connected = False

        # --- diagnostics state ---
        self.last_seen: datetime | None = None
        self.last_disconnect: datetime | None = None
        self.disconnect_count = 0
        self.reconnect_count = 0
        self._online_since: datetime | None = None
        self._offline_since: datetime | None = None
        self._last_offline_duration: timedelta | None = None
        # True while we consider the device online; used to count each
        # interruption exactly once.
        self._online = False

        self._debounce_cancel: CALLBACK_TYPE | None = None
        self._debounce_job = HassJob(self._async_emit, "ld2450_ble emit")
        self._stale_cancel: CALLBACK_TYPE | None = None
        self._stale_job = HassJob(self._handle_stale, "ld2450_ble stale")
        self._heartbeat_cancel: CALLBACK_TYPE | None = None

        device.register_callback(self._handle_update)
        device.register_disconnected_callback(self._handle_disconnect)

    @callback
    def async_start(self) -> None:
        """Start the periodic diagnostic refresh.

        Called once after setup succeeds. Keeps duration/state diagnostics
        current while the device is idle or offline (no push updates arrive
        then). Kept out of ``__init__`` so a failed setup leaves no timer.
        """
        if self._heartbeat_cancel is None:
            self._heartbeat_cancel = async_track_time_interval(
                self.hass,
                self._async_heartbeat,
                timedelta(seconds=DIAGNOSTIC_REFRESH_INTERVAL),
            )

    # ------------------------------------------------------------- callbacks

    @callback
    def _handle_update(self) -> None:
        """Handle a new valid data packet from the device."""
        now = dt_util.utcnow()
        if not self._online:
            # Transition offline -> online.
            if self.last_seen is not None:
                # Not the very first connection: this is a reconnection.
                self.reconnect_count += 1
            if self._offline_since is not None:
                self._last_offline_duration = now - self._offline_since
                self._offline_since = None
            self._online_since = now
            self._online = True
        self.last_seen = now
        self.connected = True
        # Debounced listener notification for the rapid data bursts.
        if self._debounce_cancel is None:
            self._debounce_cancel = async_call_later(
                self.hass, UPDATE_DEBOUNCE, self._debounce_job
            )

    @callback
    def _async_emit(self, _now=None) -> None:
        """Flush the debounced update to listeners."""
        self._debounce_cancel = None
        # (Re)arm stale detection relative to the most recent data.
        self._schedule_stale()
        self.async_set_updated_data(None)

    @callback
    def _schedule_stale(self) -> None:
        """(Re)schedule the stale watchdog."""
        if self._stale_cancel is not None:
            self._stale_cancel()
        self._stale_cancel = async_call_later(self.hass, STALE_TIMEOUT, self._stale_job)

    @callback
    def _handle_stale(self, _now=None) -> None:
        """Fire when no data has arrived for STALE_TIMEOUT seconds."""
        self._stale_cancel = None
        # connection_state recomputes to "stale"; just refresh listeners.
        self.async_update_listeners()

    @callback
    def _handle_disconnect(self) -> None:
        """Handle a device disconnect (count each interruption once)."""
        now = dt_util.utcnow()
        if self._online:
            self.disconnect_count += 1
            self.last_disconnect = now
            self._offline_since = now
            self._online_since = None
            self._online = False
        self.connected = False
        if self._stale_cancel is not None:
            self._stale_cancel()
            self._stale_cancel = None
        self.async_update_listeners()

    @callback
    def _async_heartbeat(self, _now=None) -> None:
        """Refresh time-based diagnostics while idle or offline."""
        self.async_update_listeners()

    # ------------------------------------------------ diagnostic properties

    @property
    def connection_state(self) -> str:
        """Return the current connection state."""
        now = dt_util.utcnow()
        if self.device.is_connected:
            if (
                self.last_seen is not None
                and (now - self.last_seen).total_seconds() > STALE_TIMEOUT
            ):
                return STATE_STALE
            return STATE_CONNECTED
        if (
            self._offline_since is not None
            and (now - self._offline_since).total_seconds() < RECONNECT_GRACE
        ):
            return STATE_RECONNECTING
        return STATE_DISCONNECTED

    @property
    def ble_connected(self) -> bool:
        """Return True only when connected with fresh data."""
        return self.connection_state == STATE_CONNECTED

    @property
    def online_duration(self) -> int:
        """Duration of the current online phase in seconds (0 if offline)."""
        if self.device.is_connected and self._online_since is not None:
            return int((dt_util.utcnow() - self._online_since).total_seconds())
        return 0

    @property
    def offline_duration(self) -> int:
        """Duration of the current or last offline phase in seconds."""
        now = dt_util.utcnow()
        if not self.device.is_connected and self._offline_since is not None:
            return int((now - self._offline_since).total_seconds())
        if self._last_offline_duration is not None:
            return int(self._last_offline_duration.total_seconds())
        return 0

    async def async_shutdown(self) -> None:
        """Cancel pending work on shutdown."""
        if self._debounce_cancel is not None:
            self._debounce_cancel()
            self._debounce_cancel = None
        if self._stale_cancel is not None:
            self._stale_cancel()
            self._stale_cancel = None
        if self._heartbeat_cancel is not None:
            self._heartbeat_cancel()
            self._heartbeat_cancel = None
        await super().async_shutdown()
