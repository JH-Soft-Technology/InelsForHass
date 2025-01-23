"""Shutter platform for inels."""
import logging

from pyinels.device.pyShutter import pyShutter
from pyinels.pyTimer import TimerError

from homeassistant.components.cover import (
    CoverEntity,
    STATE_CLOSED,
    STATE_OPEN,
    STATE_CLOSING,
    STATE_OPENING
)

from custom_components.inels_rpc.const import (
    CLASS_SHUTTER,
    DOMAIN,
    DOMAIN_DATA,
    ICON_SHUTTER_CLOSED,
    ICON_SHUTTER_OPENED,
)

from custom_components.inels_rpc.entity import InelsEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup shutter platform."""

    _LOGGER.info("Setting up shutters")

    entities = hass.data[DOMAIN][DOMAIN_DATA]
    coordinator = hass.data[DOMAIN][entry.entry_id]

    shutters = [pyShutter(dev) for dev in entities if dev.type == CLASS_SHUTTER]

    await coordinator.async_refresh()

    if len(shutters) > 0:
        async_add_devices(
            [InelsShutter(coordinator, shutter) for shutter in shutters], True
        )


class InelsShutter(InelsEntity, CoverEntity):
    """Inels shutter class."""

    def __init__(self, coordinator, shutter):
        """Initialization of the InelsShutter."""
        super().__init__(coordinator, shutter)

        self._shutter = shutter
        self._coordinator = coordinator
        self._state = STATE_CLOSED

    @property
    def name(self):
        """Device name."""
        return self._shutter.name

    @property
    def icon(self):
        """Return the icon of this shutter."""
        return (
            ICON_SHUTTER_CLOSED
            if self.current_cover_position == 0
            else ICON_SHUTTER_OPENED
        )

    @property
    def is_opening(self):
        """Shutter is opening."""
        return self._shutter.state == STATE_OPENING

    @property
    def is_closing(self):
        """Shutter is closing."""
        return self._shutter.state == STATE_CLOSING

    @property
    def is_closed(self):
        """Shutter is closed."""
        return self._shutter.state == STATE_CLOSED

    @property
    def current_cover_position(self):
        """Current cover position."""
        return self._shutter.current_position

    @property
    def device_class(self):
        """Shutter device class."""
        return CLASS_SHUTTER

    @property
    def state(self):
        """Overided state CoverEntity."""
        S = self  # constant

        result = (
            STATE_OPENING
            if S.is_opening
            else STATE_CLOSING
            if S.is_closing
            else STATE_CLOSED
            if S.is_closed
            else STATE_OPEN
            if S.device.state == STATE_OPEN
            else STATE_CLOSED
        )

        return result

    async def async_set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        self._shutter.position = kwargs["position"]

    async def async_open_cover(self, **kwargs):
        """Open the shutter."""
        await self.hass.async_add_executor_job(self._shutter.pull_up)
        await self._coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs):
        """Close shutter."""
        await self.hass.async_add_executor_job(self._shutter.pull_down)
        await self._coordinator.async_request_refresh()

    async def async_stop_cover(self, **kwargs):
        """Stop the shutter."""
        try:
            await self.hass.async_add_executor_job(self._shutter.stop)
            await self._coordinator.async_request_refresh()
        except TimerError:
            pass
