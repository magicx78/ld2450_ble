"""Async BLE engine for the HLK-LD2450 mmWave radar.

Talks to the sensor over its FFF1 (notify) / FFF2 (write) characteristics via
``bleak`` 3.x and ``bleak-retry-connector``. Works behind an ESPHome Bluetooth
proxy: the :class:`BLEDevice` is refreshed from advertisements by the HA side
through :meth:`set_ble_device_and_advertisement_data`.
"""

from __future__ import annotations

import asyncio
import logging
import struct
from collections.abc import Callable

from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak_retry_connector import (
    BLEAK_RETRY_EXCEPTIONS as BLEAK_EXCEPTIONS,
    BleakClientWithServiceCache,
    BleakNotFoundError,
    establish_connection,
)

from .const import (
    CHARACTERISTIC_NOTIFY,
    CHARACTERISTIC_WRITE,
    CMD_END_CONFIG,
    CMD_ENABLE_CONFIG,
    CMD_HEADER,
    CMD_MULTI_TARGET,
    CMD_RESTART,
    CMD_SINGLE_TARGET,
    CMD_TAIL,
    FRAME_HEADER,
    FRAME_LENGTH,
    FRAME_TAIL,
    MULTI_TARGET_MODE,
)
from .exceptions import CharacteristicMissingError
from .models import LD2450BLEConfig, LD2450BLEState, parse_target_frame

_LOGGER = logging.getLogger(__name__)

# Re-export for callers (config flow / __init__).
__all__ = ["BLEAK_EXCEPTIONS", "LD2450BLE", "LD2450BLEState", "LD2450BLEConfig"]


class LD2450BLE:
    """Connection manager and protocol handler for an LD2450 over BLE."""

    def __init__(
        self,
        ble_device: BLEDevice,
        advertisement_data: AdvertisementData | None = None,
    ) -> None:
        """Initialise the engine with a discovered BLE device."""
        self._ble_device = ble_device
        self._advertisement_data = advertisement_data
        self._client: BleakClientWithServiceCache | None = None
        self._connect_lock = asyncio.Lock()
        self._operation_lock = asyncio.Lock()
        self._buffer = bytearray()
        self._state = LD2450BLEState()
        self._config = LD2450BLEConfig(target_mode=MULTI_TARGET_MODE)
        self._expected_disconnect = False
        self._callbacks: list[Callable[[], None]] = []
        self._disconnected_callbacks: list[Callable[[], None]] = []
        self._loop = asyncio.get_running_loop()

    # ------------------------------------------------------------------ props

    @property
    def name(self) -> str:
        """Return a human friendly name for the device."""
        return self._ble_device.name or self._ble_device.address

    @property
    def address(self) -> str:
        """Return the device's Bluetooth address."""
        return self._ble_device.address

    @property
    def rssi(self) -> int | None:
        """Return the last known RSSI, if available."""
        if self._advertisement_data:
            return self._advertisement_data.rssi
        return None

    @property
    def state(self) -> LD2450BLEState:
        """Return the latest decoded target state."""
        return self._state

    @property
    def config(self) -> LD2450BLEConfig:
        """Return the current device configuration."""
        return self._config

    # ------------------------------------------------------------- callbacks

    def register_callback(self, callback: Callable[[], None]) -> Callable[[], None]:
        """Register a callback fired on every new state/config update."""
        self._callbacks.append(callback)

        def _unregister() -> None:
            self._callbacks.remove(callback)

        return _unregister

    def register_disconnected_callback(
        self, callback: Callable[[], None]
    ) -> Callable[[], None]:
        """Register a callback fired when the device disconnects."""
        self._disconnected_callbacks.append(callback)

        def _unregister() -> None:
            self._disconnected_callbacks.remove(callback)

        return _unregister

    def _fire_callbacks(self) -> None:
        for callback in self._callbacks:
            callback()

    def _fire_disconnected_callbacks(self) -> None:
        for callback in self._disconnected_callbacks:
            callback()

    def set_ble_device_and_advertisement_data(
        self, ble_device: BLEDevice, advertisement_data: AdvertisementData
    ) -> None:
        """Update the cached BLE device/advertisement (from HA's BT manager)."""
        self._ble_device = ble_device
        self._advertisement_data = advertisement_data

    # -------------------------------------------------------------- lifecycle

    async def initialise(self) -> None:
        """Connect and subscribe to notifications."""
        await self._ensure_connected()

    async def stop(self) -> None:
        """Disconnect and stop reconnect attempts."""
        _LOGGER.debug("%s: Stopping", self.name)
        self._expected_disconnect = True
        if self._client is not None:
            async with self._connect_lock:
                client = self._client
                self._client = None
                if client is not None:
                    await client.disconnect()

    async def _ensure_connected(self) -> None:
        """Ensure a live connection with notifications running."""
        if self._client is not None and self._client.is_connected:
            return
        async with self._connect_lock:
            # Re-check after acquiring the lock.
            if self._client is not None and self._client.is_connected:
                return
            _LOGGER.debug("%s: Connecting", self.name)
            client = await establish_connection(
                BleakClientWithServiceCache,
                self._ble_device,
                self.name,
                disconnected_callback=self._disconnected,
                use_services_cache=True,
                ble_device_callback=lambda: self._ble_device,
            )
            _LOGGER.debug("%s: Connected", self.name)
            self._client = client
            self._expected_disconnect = False
            try:
                await client.start_notify(
                    CHARACTERISTIC_NOTIFY, self._notification_handler
                )
            except (KeyError, ValueError) as err:
                await client.disconnect()
                self._client = None
                raise CharacteristicMissingError(
                    f"{CHARACTERISTIC_NOTIFY} characteristic missing"
                ) from err

    def _disconnected(self, client: BleakClientWithServiceCache) -> None:
        """Handle an unexpected or expected disconnect."""
        self._fire_disconnected_callbacks()
        if self._expected_disconnect:
            _LOGGER.debug("%s: Expected disconnect", self.name)
            return
        _LOGGER.debug("%s: Unexpected disconnect, scheduling reconnect", self.name)
        self._client = None
        self._loop.create_task(self._reconnect())

    async def _reconnect(self) -> None:
        """Attempt to re-establish the connection after a drop."""
        if self._expected_disconnect:
            return
        try:
            await self._ensure_connected()
        except BleakNotFoundError:
            _LOGGER.debug("%s: Device not found during reconnect", self.name)
        except BLEAK_EXCEPTIONS as err:
            _LOGGER.debug("%s: Reconnect failed: %s", self.name, err)

    # --------------------------------------------------------------- notify

    def _notification_handler(
        self, _sender: BleakGATTCharacteristic, data: bytearray
    ) -> None:
        """Handle a GATT notification, extracting complete data frames."""
        self._buffer += data
        updated = False
        while True:
            idx = self._buffer.find(FRAME_HEADER)
            if idx == -1:
                # Keep a possible partial header tail, drop the rest.
                if len(self._buffer) >= len(FRAME_HEADER):
                    del self._buffer[: -(len(FRAME_HEADER) - 1)]
                break
            if idx > 0:
                del self._buffer[:idx]
            if len(self._buffer) < FRAME_LENGTH:
                break
            frame = bytes(self._buffer[:FRAME_LENGTH])
            if frame.endswith(FRAME_TAIL):
                state = parse_target_frame(frame)
                if state is not None:
                    self._state = state
                    updated = True
                del self._buffer[:FRAME_LENGTH]
            else:
                # Header matched but tail did not: resync past this header.
                del self._buffer[:1]
        if updated:
            self._fire_callbacks()

    # -------------------------------------------------------------- commands

    async def _write(self, command: bytes) -> None:
        if self._client is None:
            raise CharacteristicMissingError("Not connected")
        await self._client.write_gatt_char(
            CHARACTERISTIC_WRITE, command, response=False
        )

    async def _send_config_command(self, command: bytes) -> None:
        """Wrap a command in the enable/end-config handshake."""
        await self._ensure_connected()
        async with self._operation_lock:
            await self._write(CMD_ENABLE_CONFIG)
            await asyncio.sleep(0.1)
            await self._write(command)
            await asyncio.sleep(0.1)
            await self._write(CMD_END_CONFIG)

    async def async_set_target_mode(self, mode: int) -> None:
        """Switch between single- and multi-target tracking."""
        command = CMD_MULTI_TARGET if mode == MULTI_TARGET_MODE else CMD_SINGLE_TARGET
        await self._send_config_command(command)
        self._config = LD2450BLEConfig(
            target_mode=mode,
            fw_ver=self._config.fw_ver,
            mac_addr=self._config.mac_addr,
            area_mode=self._config.area_mode,
            area_vertices=self._config.area_vertices,
        )
        self._fire_callbacks()

    async def async_set_area(self, mode: int, vertices: tuple[int, ...]) -> None:
        """Configure the area filter.

        Best-effort against documented command word 0x00C2 (mode + 3 regions of
        two int16 vertices). Local state is authoritative for the UI; device
        acceptance should be verified on real hardware.
        """
        command = self._build_area_command(mode, vertices)
        await self._send_config_command(command)
        self._config = LD2450BLEConfig(
            target_mode=self._config.target_mode,
            fw_ver=self._config.fw_ver,
            mac_addr=self._config.mac_addr,
            area_mode=mode,
            area_vertices=tuple(vertices),
        )
        self._fire_callbacks()

    async def async_reboot(self) -> None:
        """Restart the sensor module."""
        await self._send_config_command(CMD_RESTART)

    @staticmethod
    def _build_area_command(mode: int, vertices: tuple[int, ...]) -> bytes:
        """Build the area-filter command frame for command word 0x00C2."""
        payload = struct.pack("<H", mode)
        payload += b"".join(struct.pack("<h", int(v)) for v in vertices)
        body = b"\xc2\x00" + payload
        return CMD_HEADER + struct.pack("<H", len(body)) + body + CMD_TAIL
