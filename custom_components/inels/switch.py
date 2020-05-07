"""Switch platform for inels."""
import logging

from pyinels.device.pySwitch import pySwitch
from homeassistant.components.switch import SwitchDevice

from custom_components.inels.const import (
    DOMAIN,
    DOMAIN_DATA,
    ICON,
    SWITCH,
)
from custom_components.inels.entity import InelsEntity


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""

    _LOGGER.info("Setting up switches")

    devices = hass.data[DOMAIN][DOMAIN_DATA]
    coordinator = hass.data[DOMAIN][entry.entry_id]

    switches = [pySwitch(dev) for dev in devices if dev.type == SWITCH]

    async_add_devices([InelsSwitch(coordinator, switch) for switch in switches], True)


class InelsSwitch(InelsEntity, SwitchDevice):
    """inels switch class."""

    async def async_turn_on(self, **kwargs):  # pylint: disable=unused-argument
        """Turn on the switch."""
        self.device.turn_on()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):  # pylint: disable=unused-argument
        """Turn off the switch."""
        self.device.turn_off()
        await self.coordinator.async_request_refresh()

    @property
    def name(self):
        """Return the name of the switch."""
        return "XY"

    @property
    def icon(self):
        """Return the icon of this switch."""
        return ICON

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return self.device.state
