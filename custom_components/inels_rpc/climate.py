"""Climate platform of the iNELS integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from pyinels.device.pyTherm import pyTherm

from . import InelsConfigEntry
from .const import TYPE_THERM
from .entity import InelsEntity

PARALLEL_UPDATES = 1

# The central unit switches the level with a delay of several seconds.
LEVEL_PENDING_TIMEOUT = 20


async def async_setup_entry(
    hass: HomeAssistant,
    entry: InelsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the heat controls."""
    coordinator = entry.runtime_data
    async_add_entities(
        InelsClimate(coordinator, pyTherm(dev))
        for dev in coordinator.devices
        if dev.type == TYPE_THERM
    )


class InelsClimate(InelsEntity, ClimateEntity):
    """Heat control of a room.

    The set point is computed by the central unit from the active level,
    so the heating is controlled by the preset mode (level) only."""

    _attr_name = None
    _attr_translation_key = "heat_control"
    _attr_hvac_modes = [HVACMode.HEAT]
    _attr_hvac_mode = HVACMode.HEAT
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 0.5

    device: pyTherm

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Levels can be selected only when they are exported."""
        if self.device.levels:
            return ClimateEntityFeature.PRESET_MODE
        return ClimateEntityFeature(0)

    @property
    def current_temperature(self) -> float | None:
        """Return the measured temperature."""
        return self.device.current_temperature

    @property
    def target_temperature(self) -> float | None:
        """Return the set point."""
        return self.device.target_temperature

    @property
    def preset_modes(self) -> list[str] | None:
        """Return the levels of the heat control."""
        return self.device.levels or None

    @property
    def preset_mode(self) -> str | None:
        """Return the active level."""
        return self._value(self.device.level)

    def _actual_value(self) -> Any:
        return self.device.level

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Select the level of the heat control."""
        await self._async_write(self.device.set_level, preset_mode)
        self._set_pending(preset_mode, timeout=LEVEL_PENDING_TIMEOUT)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Heat control supports the heat mode only."""
