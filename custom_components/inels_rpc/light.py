"""Light platform of the iNELS integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from pyinels.const import RANGE_BRIGHTNESS
from pyinels.device.pyLight import pyLight

from . import InelsConfigEntry
from .const import TYPE_LIGHT
from .entity import InelsEntity

PARALLEL_UPDATES = 1

MIN_BRIGHTNESS = RANGE_BRIGHTNESS[0]
MAX_BRIGHTNESS = RANGE_BRIGHTNESS[1]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: InelsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the lights."""
    coordinator = entry.runtime_data
    lights = [pyLight(dev) for dev in coordinator.devices_of_type(TYPE_LIGHT)]
    async_add_entities(
        (
            InelsLightDimmable(coordinator, light)
            if light.has_brightness
            else InelsLight(coordinator, light)
        )
        for light in lights
    )


class InelsLight(InelsEntity, LightEntity):
    """On/off light."""

    _attr_name = None
    _attr_translation_key = "light"
    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    device: pyLight

    @property
    def is_on(self) -> bool:
        """Return true if the light is on."""
        return self._value(self.device.state)

    def _actual_value(self) -> Any:
        return self.device.state

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        await self._async_write(self.device.turn_on)
        self._set_pending(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        await self._async_write(self.device.turn_off)
        self._set_pending(False)


class InelsLightDimmable(InelsLight):
    """Dimmable light, iNELS brightness is 0-100 %."""

    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    @property
    def brightness(self) -> int:
        """Return the brightness of the light."""
        return round(self._value(self.device.brightness()) * 255 / MAX_BRIGHTNESS)

    @property
    def is_on(self) -> bool:
        """Return true if the light is on."""
        return self._value(self.device.brightness()) > MIN_BRIGHTNESS

    def _actual_value(self) -> Any:
        return self.device.brightness()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light, optionally with the brightness."""
        if ATTR_BRIGHTNESS in kwargs:
            brightness = round(kwargs[ATTR_BRIGHTNESS] * MAX_BRIGHTNESS / 255)
            await self._async_write(self.device.set_brightness, float(brightness))
        else:
            brightness = MAX_BRIGHTNESS
            await self._async_write(self.device.turn_on)
        self._set_pending(brightness)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        await self._async_write(self.device.turn_off)
        self._set_pending(MIN_BRIGHTNESS)
