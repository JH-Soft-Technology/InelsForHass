"""Light platform for inels."""
import logging

from pyinels.device.pyLight import pyLight

try:
    from homeassistant.components.light import LightEntity
except:
    from homeassistant.components.light import Light as LightEntity

from custom_components.inels.const import (
    DOMAIN,
    DOMAIN_DATA,
    ICON_LIGHT,
    LIGHT,
)

from custom_components.inels.entity import InelsEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""

    _LOGGER.info("Setting up lights")

    devices = hass.data[DOMAIN][DOMAIN_DATA]
    coordinator = hass.data[DOMAIN][entry.entry_id]

    lights = [pyLight(dev) for dev in devices if dev.type == LIGHT]

    async_add_devices([InelsLight(coordinator, light) for light in lights], True)


class InelsLight(InelsEntity, LightEntity):
    """Inels light class."""

    async def async_turn_on(self, **kwargs):  # pylint: disable=unused-argument
        """Turn on the light."""
        self.device.turn_on()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):  # pylint: disable=unused-argument
        """Turn off the light."""
        self.device.turn_off()
        await self.coordinator.async_request_refresh()

    @property
    def name(self):
        """Return the name of the light."""
        return self.device.name

    @property
    def icon(self):
        """Return the icon of this light."""
        return ICON_LIGHT

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return self.device.state
