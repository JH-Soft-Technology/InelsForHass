"""Light platform for inels."""
import logging

from pyinels.device.pyLight import pyLight
from pyinels.const import RANGE_BRIGHTNESS

try:
    from homeassistant.components.light import LightEntity
except:
    from homeassistant.components.light import Light as LightEntity

from homeassistant.components.light import ATTR_BRIGHTNESS, SUPPORT_BRIGHTNESS

from custom_components.inels.const import DOMAIN, DOMAIN_DATA, ICON_LIGHT, LIGHT

from custom_components.inels.entity import InelsEntity

_LOGGER = logging.getLogger(__name__)

MIN_BRIGHTNESS = RANGE_BRIGHTNESS[0]
MAX_BRIGHTNESS = RANGE_BRIGHTNESS[1]


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""

    _LOGGER.info("Setting up lights")

    devices = hass.data[DOMAIN][DOMAIN_DATA]
    coordinator = hass.data[DOMAIN][entry.entry_id]

    lights = [pyLight(dev) for dev in devices if dev.type == LIGHT]

    async_add_devices([InelsLight(coordinator, light) for light in lights], True)


class InelsLight(InelsEntity, LightEntity):
    """Inels light class."""

    def __init__(self, coordinator, light):
        """Initialize of the InelsLight."""
        super().__init__(coordinator, light)

        self._brightness = None
        self._features = 0
        self._light = light
        self._coordinator = coordinator
        self._has_brightness = self._light.has_brightness
        self._state = self._light.state

        if self._has_brightness is True:
            self._features = SUPPORT_BRIGHTNESS

    async def async_turn_on(self, **kwargs):  # pylint: disable=unused-argument
        """Turn on the light."""
        brightness = 0

        if ATTR_BRIGHTNESS in kwargs:
            brightness = int(kwargs[ATTR_BRIGHTNESS] / 2.55)
            self._brightness = brightness
            self._light.set_brightness(float(brightness))
            self._state = self._light.state
        else:
            self._light.turn_on()
            self._brightness = MAX_BRIGHTNESS
            self._state = True

        await self._coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):  # pylint: disable=unused-argument
        """Turn off the light."""
        self._light.turn_off()
        self._state = False
        await self._coordinator.async_request_refresh()

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
        """Return true if the switch is on."""
        return self._state

    @property
    def supported_features(self):
        """Supported feature of the light. We support brightnes.
        In future maybee i RGB and temperature."""
        return self._features

    @property
    def brightness(self):
        """Return the brightness of the light."""
        if self._has_brightness is True:
            if self._brightness is None:
                self._brightness = self._light.brightness()

            return int(self._brightness * 2.55)
        return None

    def update(self):
        """Fetch new state data for light."""
        self._state = self._light.state

        if self._has_brightness is True:
            self._brightness = self._light.brightness
