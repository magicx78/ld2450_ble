"""Base entity for the LD2450 BLE integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import LD2450BLECoordinator


class LD2450BLEEntity(CoordinatorEntity[LD2450BLECoordinator]):
    """Base entity that ties all platforms to one device."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: LD2450BLECoordinator, key: str
    ) -> None:
        """Initialise the entity with a stable unique id."""
        super().__init__(coordinator)
        address = coordinator.device.address
        self._attr_unique_id = f"{address}_{key}"
        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, address)},
            identifiers={(DOMAIN, address)},
            name=coordinator.config_entry.title,
            manufacturer="HiLink",
            model="LD2450",
        )

    @property
    def available(self) -> bool:
        """Return True only while the device is connected."""
        return self.coordinator.connected and super().available

    @property
    def device(self):
        """Shortcut to the BLE device handle."""
        return self.coordinator.device
