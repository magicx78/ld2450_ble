"""Binary sensor platform for the LD2450 BLE integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .ld2450_ble.models import LD2450BLEState
from .coordinator import LD2450BLECoordinator
from .entity import LD2450BLEEntity
from .models import LD2450BLEConfigEntry

TARGET_COUNT = 3


@dataclass(frozen=True, kw_only=True)
class LD2450BLEBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes an LD2450 binary sensor."""

    is_on_fn: Callable[[LD2450BLEState], bool]


PRESENCE_SENSOR = LD2450BLEBinarySensorEntityDescription(
    key="any_presence",
    translation_key="any_presence",
    device_class=BinarySensorDeviceClass.OCCUPANCY,
    is_on_fn=lambda state: state.any_present,
)


def _target_sensors(index: int) -> tuple[LD2450BLEBinarySensorEntityDescription, ...]:
    """Build the present/moving descriptions for one target slot."""
    return (
        LD2450BLEBinarySensorEntityDescription(
            key=f"target{index + 1}_present",
            translation_key="target_present",
            device_class=BinarySensorDeviceClass.OCCUPANCY,
            is_on_fn=lambda state, i=index: state.targets[i].present,
        ),
        LD2450BLEBinarySensorEntityDescription(
            key=f"target{index + 1}_moving",
            translation_key="target_moving",
            device_class=BinarySensorDeviceClass.MOVING,
            is_on_fn=lambda state, i=index: state.targets[i].moving,
        ),
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LD2450BLEConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor platform."""
    coordinator = entry.runtime_data.coordinator
    entities: list[LD2450BLEBinarySensor] = [
        LD2450BLEBinarySensor(coordinator, PRESENCE_SENSOR)
    ]
    for index in range(TARGET_COUNT):
        for description in _target_sensors(index):
            entities.append(
                LD2450BLEBinarySensor(coordinator, description, index)
            )
    async_add_entities(entities)


class LD2450BLEBinarySensor(LD2450BLEEntity, BinarySensorEntity):
    """A binary sensor for presence/movement."""

    entity_description: LD2450BLEBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: LD2450BLECoordinator,
        description: LD2450BLEBinarySensorEntityDescription,
        index: int | None = None,
    ) -> None:
        """Initialise the binary sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description
        if index is not None:
            self._attr_translation_placeholders = {"target": str(index + 1)}

    @property
    def is_on(self) -> bool:
        """Return True if the binary sensor is active."""
        return self.entity_description.is_on_fn(self.coordinator.device.state)
