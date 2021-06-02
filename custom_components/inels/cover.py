"""Shutter platform for inels."""
import logging

from pyinels.device.pyShutter import pyShutter
from pyinels.pyTimer import TimerError

from pyinels.const import (
    SUPPORT_OPEN,
    SUPPORT_CLOSE,
    SUPPORT_SET_POSITION,
    SUPPORT_STOP,
    STATE_OPEN,
    STATE_CLOSED,
    STATE_OPENING,
    STATE_CLOSING,
)

from homeassistant.components.cover import CoverEntity

from custom_components.inels.const import (
    DOMAIN,
    DOMAIN_DATA,
    ICON_SHUTTER,
    DEVICE_CLASS_SHUTTER,
)

from custom_components.inels.entity import InelsEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup shutter platform."""

    _LOGGER.info("Setting up shutters")

    entities = hass.data[DOMAIN][DOMAIN_DATA]
    coordinator = hass.data[DOMAIN][entry.entry_id]

    shutters = [pyShutter(dev) for dev in entities if dev.type == DEVICE_CLASS_SHUTTER]

    if len(shutters) > 0:
        async_add_devices(
            [InelsShutter(coordinator, shutter) for shutter in shutters], True
        )


class InelsShutter(InelsEntity, CoverEntity):
    """Inels shutter class."""

    @property
    def name(self):
        """Device name."""
        return self.device.name

    @property
    def icon(self):
        """Return the icon of this shutter."""
        return ICON_SHUTTER

    @property
    def supported_features(self):
        """Supported features."""
        return SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_SET_POSITION | SUPPORT_STOP

    @property
    def is_opening(self):
        """Shutter is opening."""
        return self.device.state == STATE_OPENING

    @property
    def is_closing(self):
        """Shutter is closing."""
        return self.device.state == STATE_CLOSING

    @property
    def is_closed(self):
        """Shutter is closed."""
        return self.device.state == STATE_CLOSED

    @property
    def current_cover_position(self):
        """Current cover position."""
        return self.device.current_position

    # @property
    # def state(self):
    #     """Overided state CoverEntity."""
    #     S = self  # constant

    #     result = (
    #         STATE_OPENING
    #         if S.is_opening
    #         else STATE_CLOSING
    #         if S.is_closing
    #         else STATE_CLOSED
    #         if S.is_closed
    #         else STATE_OPEN
    #         if S.device.state == STATE_OPEN
    #         else STATE_CLOSED
    #     )

    #     return result

    async def async_set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        self.device.position = kwargs["position"]

    async def async_open_cover(self, **kwargs):
        """Open the shutter."""
        self.device.pull_up()

    async def async_close_cover(self, **kwargs):
        """Close shutter."""
        self.device.pull_down()

    async def async_stop_cover(self, **kwargs):
        """Stop the shutter."""
        try:
            self.device.stop()
        except TimerError:
            pass