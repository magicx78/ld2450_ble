"""Number platform for the LD2450 BLE integration (area-filter vertices)."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import EntityCategory, UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .ld2450_ble.models import with_area_vertex
from .coordinator import LD2450BLECoordinator
from .entity import LD2450BLEEntity
from .models import LD2450BLEConfigEntry

# area_vertices layout: 3 regions x (x1, y1, x2, y2) = 12 values.
# Even local offset -> X axis, odd -> Y axis.
AREA_COUNT = 3


@dataclass(frozen=True, kw_only=True)
class LD2450BLENumberEntityDescription(NumberEntityDescription):
    """Describes an area-vertex number entity."""

    vertex_index: int


def _build_descriptions() -> tuple[LD2450BLENumberEntityDescription, ...]:
    """Build the 12 area-vertex number descriptions."""
    descriptions: list[LD2450BLENumberEntityDescription] = []
    for area in range(AREA_COUNT):
        for corner in range(2):  # two vertices per area
            for axis, name in enumerate(("x", "y")):
                index = area * 4 + corner * 2 + axis
                is_x = axis == 0
                descriptions.append(
                    LD2450BLENumberEntityDescription(
                        key=f"area{area + 1}_v{corner + 1}_{name}",
                        translation_key=f"area_vertex_{name}",
                        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
                        native_min_value=-5000 if is_x else 0,
                        native_max_value=5000 if is_x else 7300,
                        native_step=100,
                        mode=NumberMode.SLIDER,
                        entity_category=EntityCategory.CONFIG,
                        entity_registry_enabled_default=False,
                        vertex_index=index,
                    )
                )
    return tuple(descriptions)


NUMBER_TYPES = _build_descriptions()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LD2450BLEConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the number platform."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        LD2450BLEAreaVertexNumber(coordinator, description)
        for description in NUMBER_TYPES
    )


class LD2450BLEAreaVertexNumber(LD2450BLEEntity, NumberEntity):
    """A single area-filter vertex coordinate."""

    entity_description: LD2450BLENumberEntityDescription

    def __init__(
        self,
        coordinator: LD2450BLECoordinator,
        description: LD2450BLENumberEntityDescription,
    ) -> None:
        """Initialise the number entity."""
        super().__init__(coordinator, description.key)
        self.entity_description = description
        area = description.vertex_index // 4 + 1
        corner = (description.vertex_index % 4) // 2 + 1
        self._attr_translation_placeholders = {
            "area": str(area),
            "vertex": str(corner),
        }

    @property
    def native_value(self) -> float:
        """Return the current vertex coordinate."""
        return self.coordinator.device.config.area_vertices[
            self.entity_description.vertex_index
        ]

    async def async_set_native_value(self, value: float) -> None:
        """Update one vertex coordinate and re-send the area config."""
        config = self.coordinator.device.config
        new_config = with_area_vertex(
            config, self.entity_description.vertex_index, int(value)
        )
        await self.coordinator.device.async_set_area(
            new_config.area_mode, new_config.area_vertices
        )
