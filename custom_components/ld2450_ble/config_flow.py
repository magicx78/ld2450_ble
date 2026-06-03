"""Config flow for the LD2450 BLE integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from bluetooth_data_tools import human_readable_name
from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import callback

from .const import CONF_ENABLE_RMM, DEFAULT_ENABLE_RMM, DOMAIN, LOCAL_NAMES
from .ld2450_ble import BLEAK_EXCEPTIONS, LD2450BLE

_LOGGER = logging.getLogger(__name__)


class LD2450BleConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for LD2450 BLE."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialise the flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovered_devices: dict[str, BluetoothServiceInfoBleak] = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow handler."""
        return LD2450BleOptionsFlow()

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle a flow initialised by bluetooth discovery."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        self._discovery_info = discovery_info
        self.context["title_placeholders"] = {
            "name": human_readable_name(
                None, discovery_info.name, discovery_info.address
            )
        }
        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the user / confirmation step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            discovery_info = self._discovered_devices[address]
            await self.async_set_unique_id(
                discovery_info.address, raise_on_progress=False
            )
            self._abort_if_unique_id_configured()
            device = LD2450BLE(discovery_info.device, discovery_info.advertisement)
            try:
                await device.initialise()
            except BLEAK_EXCEPTIONS:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error connecting to %s", address)
                errors["base"] = "unknown"
            else:
                await device.stop()
                return self.async_create_entry(
                    title=discovery_info.name,
                    data={CONF_ADDRESS: discovery_info.address},
                )

        if discovery := self._discovery_info:
            self._discovered_devices[discovery.address] = discovery
        else:
            await bluetooth.async_request_active_scan(self.hass)
            current_addresses = self._async_current_ids(include_ignore=False)
            for discovery in async_discovered_service_info(self.hass):
                if (
                    discovery.address in current_addresses
                    or discovery.address in self._discovered_devices
                    or not any(discovery.name.startswith(name) for name in LOCAL_NAMES)
                ):
                    continue
                self._discovered_devices[discovery.address] = discovery

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(
                        {
                            info.address: f"{info.name} ({info.address})"
                            for info in self._discovered_devices.values()
                        }
                    )
                }
            ),
            errors=errors,
        )


class LD2450BleOptionsFlow(OptionsFlow):
    """Handle options for the LD2450 BLE integration."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the integration options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(CONF_ENABLE_RMM, DEFAULT_ENABLE_RMM)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {vol.Required(CONF_ENABLE_RMM, default=current): bool}
            ),
        )
