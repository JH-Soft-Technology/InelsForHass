"""Light platform for inels."""
import logging

from pyinels.device.pyLight import pyLight
from pyinels.const import RANGE_BRIGHTNESS

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
)

from custom_components.inels_rpc.entity import InelsEntity
from custom_components.inels_rpc.const import DOMAIN, DOMAIN_DATA, ICON_LIGHT, PLATFORM_LIGHT

_LOGGER = logging.getLogger(__name__)

MIN_BRIGHTNESS = RANGE_BRIGHTNESS[0]
MAX_BRIGHTNESS = RANGE_BRIGHTNESS[1]


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup light platform."""

    _LOGGER.info("Setting up lights")

    devices = hass.data[DOMAIN][DOMAIN_DATA]
    coordinator = hass.data[DOMAIN][entry.entry_id]

    dimmable_lights = []
    usual_lights = []

    lights = [
        await hass.async_add_executor_job(pyLight, dev)
        for dev in devices
        if dev.type == PLATFORM_LIGHT
    ]

    for light in lights:
        if light.has_brightness is True:
            dimmable_lights.append(light)
        else:
            usual_lights.append(light)

    await coordinator.async_refresh()

    if len(usual_lights) > 0:
        async_add_devices(
            [InelsLight(coordinator, light) for light in usual_lights], True
        )

    if len(dimmable_lights) > 0:
        async_add_devices(
            [InelsLightDimmable(coordinator, light) for light in dimmable_lights], True
        )


class InelsLightBase(InelsEntity, LightEntity):
    """Inels base light class."""

    def __init__(self, coordinator, light):
        """Initialize of the InelsLight."""
        super().__init__(coordinator, light)

        self._light = light
        self._coordinator = coordinator
        self._state = False

    async def async_turn_on(self, **kwargs):  # pylint: disable=unused-argument
        """Turn on the light."""
        await self.hass.async_add_executor_job(self._light.turn_on)
        self._state = True

        await self._coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):  # pylint: disable=unused-argument
        """Turn off the light."""
        await self.hass.async_add_executor_job(self._light.turn_off)
        self._state = False

        await self._coordinator.async_request_refresh()

    @property
    def color_mode(self):
        """Return color mode of the light."""
        return ColorMode.ONOFF

    @property
    def supported_color_modes(self) -> set[ColorMode] | set[str] | None:
        """Flag supported color modes. Overrided."""
        return {ColorMode.ONOFF}

    @property
    def name(self):
        """Return the name of the light."""
        return self._light.name

    @property
    def icon(self):
        """Return the icon of this light."""
        return ICON_LIGHT

    @property
    def is_on(self):
        """Return true if the light is on."""
        return self._light.state

    def update(self):
        """Update the data from the device."""
        return self.update()


class InelsLight(InelsLightBase, LightEntity):
    """Inels light class."""

    def __init__(self, coordinator, light):
        """Initialize of the InelsLight."""
        super().__init__(coordinator, light)


class InelsLightDimmable(InelsLightBase, LightEntity):
    """Inels dimmable light class."""

    def __init__(self, coordinator, light):
        """Initialize of the InelsLightDimmable."""
        super().__init__(coordinator, light)

        self._brightness = None
        self._features = 0
        self._light = light
        self._coordinator = coordinator
        self._state = False

    @property
    def brightness(self):
        """Return the brightness of the light."""
        self._brightness = self._light.brightness()

        return int(self._brightness * 2.55)

    @property
    def color_mode(self):
        """Return color mode of the light."""
        return ColorMode.BRIGHTNESS

    @property
    def supported_color_modes(self) -> set[ColorMode] | set[str] | None:
        """Flag supported color modes. Overrided."""
        return {ColorMode.BRIGHTNESS}

    async def async_turn_on(self, **kwargs):  # pylint: disable=unused-argument
        """Turn on the light."""
        brightness = 0

        if ATTR_BRIGHTNESS in kwargs:
            brightness = int(kwargs[ATTR_BRIGHTNESS] / 2.55)
            self._brightness = brightness
            await self.hass.async_add_executor_job(
                self._light.set_brightness, float(brightness)
            )
            self._state = self._light.state
        else:
            await self.hass.async_add_executor_job(self._light.turn_on)
            self._brightness = MAX_BRIGHTNESS
            self._state = True

        await self._coordinator.async_request_refresh()
