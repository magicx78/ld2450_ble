"""Button platform for the LD2450 BLE integration."""

from __future__ import annotations

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import LD2450BLECoordinator
from .entity import LD2450BLEEntity
from .models import LD2450BLEConfigEntry

REBOOT_BUTTON = ButtonEntityDescription(
    key="reboot",
    translation_key="reboot",
    device_class=ButtonDeviceClass.RESTART,
    entity_category=EntityCategory.CONFIG,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LD2450BLEConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities([LD2450BLERebootButton(coordinator, REBOOT_BUTTON)])


class LD2450BLERebootButton(LD2450BLEEntity, ButtonEntity):
    """Reboot the LD2450 module."""

    entity_description: ButtonEntityDescription

    def __init__(
        self,
        coordinator: LD2450BLECoordinator,
        description: ButtonEntityDescription,
    ) -> None:
        """Initialise the button."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    async def async_press(self) -> None:
        """Reboot the device."""
        await self.coordinator.device.async_reboot()
