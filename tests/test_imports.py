"""Import-smoke tests.

The platform modules (sensor, number, ...) are only imported by Home Assistant
when an entry sets up its platforms, so the behavioural tests never load them.
These tests import every module against the installed Home Assistant so that
module-level mistakes (e.g. a non-existent ``UnitOfSpeed`` member) are caught.
"""

from __future__ import annotations

import importlib

import pytest

MODULES = [
    "__init__",
    "const",
    "models",
    "coordinator",
    "entity",
    "config_flow",
    "sensor",
    "binary_sensor",
    "switch",
    "select",
    "button",
    "number",
    "ld2450_ble.ld2450_ble",
    "ld2450_ble.models",
    "ld2450_ble.const",
    "ld2450_ble.exceptions",
]


@pytest.mark.parametrize("module", MODULES)
def test_module_imports(module: str) -> None:
    """Every integration module imports without error."""
    importlib.import_module(f"custom_components.ld2450_ble.{module}")
