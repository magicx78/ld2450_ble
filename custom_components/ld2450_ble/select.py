"""Select platform for the LD2450 BLE integration."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .ld2450_ble.const import AREA_DISABLED, AREA_IGNORE, AREA_MONITOR
from .coordinator import LD2450BLECoordinator
from .entity import LD2450BLEEntity
from .models import LD2450BLEConfigEntry

# Option label -> device mode value. Labels are translated via select state keys.
AREA_OPTIONS: dict[str, int] = {
    "disabled": AREA_DISABLED,
    "monitor": AREA_MONITOR,
    "ignore": AREA_IGNORE,
}
AREA_MODE_TO_OPTION = {value: key for key, value in AREA_OPTIONS.items()}

AREA_MODE_SELECT = SelectEntityDescription(
    key="area_mode",
    translation_key="area_mode",
    entity_category=EntityCategory.CONFIG,
    options=list(AREA_OPTIONS),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LD2450BLEConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the select platform."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities([LD2450BLEAreaModeSelect(coordinator, AREA_MODE_SELECT)])


class LD2450BLEAreaModeSelect(LD2450BLEEntity, SelectEntity):
    """Select the area-filter mode."""

    entity_description: SelectEntityDescription

    def __init__(
        self,
        coordinator: LD2450BLECoordinator,
        description: SelectEntityDescription,
    ) -> None:
        """Initialise the select."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def current_option(self) -> str | None:
        """Return the currently selected option."""
        return AREA_MODE_TO_OPTION.get(self.coordinator.device.config.area_mode)

    async def async_select_option(self, option: str) -> None:
        """Change the area-filter mode, keeping the current vertices."""
        mode = AREA_OPTIONS[option]
        vertices = self.coordinator.device.config.area_vertices
        await self.coordinator.device.async_set_area(mode, vertices)
