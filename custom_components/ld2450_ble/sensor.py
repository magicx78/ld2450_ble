"""Sensor platform for the LD2450 BLE integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import DEGREE, UnitOfLength, UnitOfSpeed
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import LD2450BLECoordinator
from .entity import LD2450BLEEntity
from .ld2450_ble.models import Target
from .models import LD2450BLEConfigEntry

TARGET_COUNT = 3


@dataclass(frozen=True, kw_only=True)
class LD2450BLESensorEntityDescription(SensorEntityDescription):
    """Describes an LD2450 sensor derived from a target."""

    value_fn: Callable[[Target], float | int]


SENSOR_TYPES: tuple[LD2450BLESensorEntityDescription, ...] = (
    LD2450BLESensorEntityDescription(
        key="distance",
        translation_key="distance",
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda t: round(t.distance),
    ),
    LD2450BLESensorEntityDescription(
        key="angle",
        translation_key="angle",
        native_unit_of_measurement=DEGREE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda t: round(t.angle, 1),
    ),
    LD2450BLESensorEntityDescription(
        key="x",
        translation_key="x",
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda t: t.x,
    ),
    LD2450BLESensorEntityDescription(
        key="y",
        translation_key="y",
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda t: t.y,
    ),
    LD2450BLESensorEntityDescription(
        key="speed",
        translation_key="speed",
        # Raw protocol unit is cm/s; HA has no cm/s speed unit, so report mm/s.
        native_unit_of_measurement=UnitOfSpeed.MILLIMETERS_PER_SECOND,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda t: t.speed * 10,
    ),
    LD2450BLESensorEntityDescription(
        key="resolution",
        translation_key="resolution",
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda t: t.resolution,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LD2450BLEConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        LD2450BLESensor(coordinator, description, index)
        for index in range(TARGET_COUNT)
        for description in SENSOR_TYPES
    )


class LD2450BLESensor(LD2450BLEEntity, SensorEntity):
    """A sensor derived from one target slot."""

    entity_description: LD2450BLESensorEntityDescription

    def __init__(
        self,
        coordinator: LD2450BLECoordinator,
        description: LD2450BLESensorEntityDescription,
        index: int,
    ) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator, f"target{index + 1}_{description.key}")
        self.entity_description = description
        self._index = index
        self._attr_translation_placeholders = {"target": str(index + 1)}

    @property
    def native_value(self) -> float | int:
        """Return the current value for this target field."""
        target = self.coordinator.device.state.targets[self._index]
        return self.entity_description.value_fn(target)
