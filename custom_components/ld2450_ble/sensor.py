"""Sensor platform for the LD2450 BLE integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import DEGREE, UnitOfLength, UnitOfSpeed, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONNECTION_STATES
from .coordinator import LD2450BLECoordinator
from .entity import LD2450BLEDiagnosticEntity, LD2450BLEEntity
from .ld2450_ble.models import Target
from .models import LD2450BLEConfigEntry

TARGET_COUNT = 3


@dataclass(frozen=True, kw_only=True)
class LD2450BLESensorEntityDescription(SensorEntityDescription):
    """Describes an LD2450 sensor derived from a target."""

    value_fn: Callable[[Target], float | int]
    # When True, report ``None`` (unknown) instead of a value for an empty
    # target slot. Used by the X/Y coordinates so downstream consumers (e.g.
    # Radar Map Manager) cleanly skip absent targets instead of seeing (0, 0).
    none_when_absent: bool = False


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
    # X/Y are enabled by default: they are the coordinates Radar Map Manager
    # reads (sensor.<device>_target_N_x / _y, in mm). Empty slots report unknown.
    LD2450BLESensorEntityDescription(
        key="x",
        translation_key="x",
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        none_when_absent=True,
        value_fn=lambda t: t.x,
    ),
    LD2450BLESensorEntityDescription(
        key="y",
        translation_key="y",
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        none_when_absent=True,
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


@dataclass(frozen=True, kw_only=True)
class LD2450BLEDiagSensorEntityDescription(SensorEntityDescription):
    """Describes a connectivity-diagnostic sensor read from the coordinator."""

    value_fn: Callable[[LD2450BLECoordinator], datetime | int | str | None]


DIAGNOSTIC_SENSOR_TYPES: tuple[LD2450BLEDiagSensorEntityDescription, ...] = (
    LD2450BLEDiagSensorEntityDescription(
        key="last_seen",
        translation_key="last_seen",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda c: c.last_seen,
    ),
    LD2450BLEDiagSensorEntityDescription(
        key="connection_state",
        translation_key="connection_state",
        device_class=SensorDeviceClass.ENUM,
        options=CONNECTION_STATES,
        value_fn=lambda c: c.connection_state,
    ),
    LD2450BLEDiagSensorEntityDescription(
        key="disconnect_count",
        translation_key="disconnect_count",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda c: c.disconnect_count,
    ),
    LD2450BLEDiagSensorEntityDescription(
        key="reconnect_count",
        translation_key="reconnect_count",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda c: c.reconnect_count,
    ),
    LD2450BLEDiagSensorEntityDescription(
        key="last_disconnect",
        translation_key="last_disconnect",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda c: c.last_disconnect,
    ),
    LD2450BLEDiagSensorEntityDescription(
        key="offline_duration",
        translation_key="offline_duration",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.offline_duration,
    ),
    LD2450BLEDiagSensorEntityDescription(
        key="online_duration",
        translation_key="online_duration",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.online_duration,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LD2450BLEConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = entry.runtime_data.coordinator
    entities: list[SensorEntity] = [
        LD2450BLESensor(coordinator, description, index)
        for index in range(TARGET_COUNT)
        for description in SENSOR_TYPES
    ]
    entities.extend(
        LD2450BLEDiagnosticSensor(coordinator, description)
        for description in DIAGNOSTIC_SENSOR_TYPES
    )
    entities.append(LD2450BLEPresenceCountSensor(coordinator))
    async_add_entities(entities)


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
    def native_value(self) -> float | int | None:
        """Return the current value for this target field."""
        target = self.coordinator.device.state.targets[self._index]
        if self.entity_description.none_when_absent and not target.present:
            return None
        return self.entity_description.value_fn(target)


class LD2450BLEDiagnosticSensor(LD2450BLEDiagnosticEntity, SensorEntity):
    """A connectivity-diagnostic sensor read from the coordinator."""

    entity_description: LD2450BLEDiagSensorEntityDescription

    def __init__(
        self,
        coordinator: LD2450BLECoordinator,
        description: LD2450BLEDiagSensorEntityDescription,
    ) -> None:
        """Initialise the diagnostic sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> datetime | int | str | None:
        """Return the current diagnostic value."""
        return self.entity_description.value_fn(self.coordinator)


class LD2450BLEPresenceCountSensor(LD2450BLEEntity, SensorEntity):
    """Number of currently present targets (0..3).

    Exposed as ``sensor.<device>_presence_target_count`` for convenience and
    Radar Map Manager compatibility. (RMM derives its own fused count, so this
    is an additive helper, not a hard requirement.)
    """

    _attr_translation_key = "presence_target_count"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: LD2450BLECoordinator) -> None:
        """Initialise the presence-count sensor."""
        super().__init__(coordinator, "presence_target_count")

    @property
    def native_value(self) -> int:
        """Return how many target slots currently hold a real detection."""
        return sum(
            1 for target in self.coordinator.device.state.targets if target.present
        )
