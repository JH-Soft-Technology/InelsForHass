"""Switch platform for inels."""
import logging

from pyinels.device.pySwitch import pySwitch
from pyinels.device.pyDoor import pyDoor

from homeassistant.components.switch import SwitchDevice

from custom_components.inels.const import (
    DOMAIN,
    DOMAIN_DATA,
    ICON_SWITCH,
    SWITCH,
    DOOR,
    ICON_DOOR,
)
from custom_components.inels.entity import InelsEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""

    _LOGGER.info("Setting up switches")

    entities = hass.data[DOMAIN][DOMAIN_DATA]
    coordinator = hass.data[DOMAIN][entry.entry_id]

    devices = [dev for dev in entities if dev.type == SWITCH or dev.type == DOOR]

    switches = [pySwitch(dev) for dev in devices if dev.type == SWITCH]
    doors = [pyDoor(dev) for dev in devices if dev.type == DOOR]

    if len(switches) > 0:
        async_add_devices(
            [InelsSwitch(coordinator, switch) for switch in switches], True
        )

    if len(doors) > 0:
        async_add_devices([InelsDoor(coordinator, door) for door in doors], True)


class InelsSwitch(InelsEntity, SwitchDevice):
    """Inels switch class."""

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
        return self.device.name

    @property
    def icon(self):
        """Return the icon of this switch."""
        return ICON_SWITCH

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return self.device.state


class InelsDoor(InelsSwitch):
    """Inels door class implements InelsSwitch."""

    @property
    def icon(self):
        """Return the icon of this door."""
        return ICON_DOOR
