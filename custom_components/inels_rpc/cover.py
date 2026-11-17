"""Cover platform of the iNELS integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from pyinels.const import STATE_CLOSED, STATE_CLOSING, STATE_OPENING
from pyinels.device.pyShutter import pyShutter

from . import InelsConfigEntry
from .const import TYPE_SHUTTER
from .entity import InelsEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: InelsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the shutters."""
    coordinator = entry.runtime_data
    async_add_entities(
        InelsShutter(coordinator, pyShutter(dev))
        for dev in coordinator.devices_of_type(TYPE_SHUTTER)
    )


class InelsShutter(InelsEntity, CoverEntity):
    """Shutter driven by the up and down relays.

    The central unit does not report the position, so only open, close
    and stop are supported. Open/closed is derived from the last movement
    and can be wrong after a stop or a restart, so the state is assumed and
    both open and close stay available."""

    _attr_name = None
    _attr_assumed_state = True
    _attr_translation_key = "shutter"
    _attr_device_class = CoverDeviceClass.SHUTTER
    _attr_supported_features = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
    )

    device: pyShutter

    @property
    def is_opening(self) -> bool:
        """Return true when the shutter is opening."""
        return self.device.state == STATE_OPENING

    @property
    def is_closing(self) -> bool:
        """Return true when the shutter is closing."""
        return self.device.state == STATE_CLOSING

    @property
    def is_closed(self) -> bool:
        """Return true when the shutter is closed."""
        return self.device.state == STATE_CLOSED

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the shutter."""
        await self._async_command(self.device.pull_up)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the shutter."""
        await self._async_command(self.device.pull_down)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the shutter."""
        await self._async_command(self.device.stop)

    async def _async_command(self, func: Any) -> None:
        """Write the command and show its result right away."""
        await self._async_write(func)
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
