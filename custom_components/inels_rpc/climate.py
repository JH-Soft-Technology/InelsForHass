"""Climate platform for inels."""

import logging

from pyinels.device.pyTherm import pyTherm

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import UnitOfTemperature

from custom_components.inels_rpc.entity import InelsEntity
from custom_components.inels_rpc.const import (
    DOMAIN,
    DOMAIN_DATA,
    ICON_THERM,
    PLATFORM_THERM,
    TRANSLATION_HEAT_CONTROL,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup climate platform."""

    _LOGGER.info("Setting up heat controls")

    devices = hass.data[DOMAIN][DOMAIN_DATA]
    coordinator = hass.data[DOMAIN][entry.entry_id]

    therms = [
        await hass.async_add_executor_job(pyTherm, dev)
        for dev in devices
        if dev.type == PLATFORM_THERM
    ]

    await coordinator.async_refresh()

    if len(therms) > 0:
        async_add_devices([InelsClimate(coordinator, therm) for therm in therms], True)


class InelsClimate(InelsEntity, ClimateEntity):
    """Inels heat control class.

    The set point is computed by the central unit from the active level,
    so the heating is controlled by the preset mode (level) only."""

    _attr_hvac_modes = [HVACMode.HEAT]
    _attr_hvac_mode = HVACMode.HEAT
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 0.5
    _attr_translation_key = TRANSLATION_HEAT_CONTROL

    @property
    def name(self):
        """Return the name of the heat control."""
        return self.device.name

    @property
    def icon(self):
        """Return the icon of the heat control."""
        return ICON_THERM

    @property
    def supported_features(self):
        """Levels can be selected only when they are exported."""
        if self.device.levels:
            return ClimateEntityFeature.PRESET_MODE
        return ClimateEntityFeature(0)

    @property
    def current_temperature(self):
        """Return the measured temperature."""
        return self.device.current_temperature

    @property
    def target_temperature(self):
        """Return the set point."""
        return self.device.target_temperature

    @property
    def preset_modes(self):
        """Return the levels of the heat control."""
        return self.device.levels or None

    @property
    def preset_mode(self):
        """Return the active level."""
        return self._value(self.device.level)

    def _actual_value(self):
        return self.device.level

    async def async_set_preset_mode(self, preset_mode):
        """Select the level of the heat control."""
        await self.hass.async_add_executor_job(self.device.set_level, preset_mode)
        self._set_pending(preset_mode, timeout=20)

    async def async_set_hvac_mode(self, hvac_mode):
        """Heat control supports the heat mode only."""
