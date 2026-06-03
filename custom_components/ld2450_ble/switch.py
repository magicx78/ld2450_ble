"""Switch platform for the LD2450 BLE integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .ld2450_ble import MULTI_TARGET_MODE, SINGLE_TARGET_MODE
from .coordinator import LD2450BLECoordinator
from .entity import LD2450BLEEntity
from .models import LD2450BLEConfigEntry

MULTI_TARGET_SWITCH = SwitchEntityDescription(
    key="multi_target",
    translation_key="multi_target",
    entity_category=EntityCategory.CONFIG,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LD2450BLEConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities([LD2450BLEMultiTargetSwitch(coordinator, MULTI_TARGET_SWITCH)])


class LD2450BLEMultiTargetSwitch(LD2450BLEEntity, SwitchEntity):
    """Switch between multi-target (on) and single-target (off) tracking."""

    entity_description: SwitchEntityDescription

    def __init__(
        self,
        coordinator: LD2450BLECoordinator,
        description: SwitchEntityDescription,
    ) -> None:
        """Initialise the switch."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool:
        """Return True when multi-target tracking is active."""
        return self.coordinator.device.config.target_mode == MULTI_TARGET_MODE

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable multi-target tracking."""
        await self.coordinator.device.async_set_target_mode(MULTI_TARGET_MODE)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Enable single-target tracking."""
        await self.coordinator.device.async_set_target_mode(SINGLE_TARGET_MODE)
