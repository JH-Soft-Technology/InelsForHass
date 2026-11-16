"""InelsEntity class"""

import time

from homeassistant.core import callback
from homeassistant.helpers import entity

from .const import DOMAIN, VERSION, TITLE

# How long a written value is kept when the polled value does not match it yet.
# The central unit applies a write with a delay, so the first read after a
# command can still return the previous value.
PENDING_TIMEOUT = 6


class InelsEntity(entity.Entity):
    def __init__(self, coordinator, device):
        self.coordinator = coordinator
        self.device = device
        self._pending = None
        self._pending_until = 0.0

    def _set_pending(self, value, timeout=PENDING_TIMEOUT):
        """Remember the value written by a command and show it right away."""
        self._pending = value
        self._pending_until = time.monotonic() + timeout
        self.async_write_ha_state()

    def _actual_value(self):
        """Value compared with the pending one; overridden by the platforms."""
        return None

    def _value(self, actual):
        """Return the pending value while the unit has not confirmed it yet."""
        if self._pending is None:
            return actual
        if actual == self._pending or time.monotonic() > self._pending_until:
            self._pending = None
            return actual
        return self._pending

    @callback
    def _handle_coordinator_update(self):
        """Drop the pending value once confirmed or expired, then write state."""
        self._value(self._actual_value())
        self.async_write_ha_state()

    @property
    def should_poll(self):
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    @property
    def available(self):
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return self.device.unique_id

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "model": type(self).__name__,
            "manufacturer": TITLE,
            "sw_version": VERSION,
            "suggested_area": self.device.group,
        }

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "inels_type": type(self.device).__name__,
            "inels_id": self.device.unique_id,
        }

    async def async_added_to_hass(self):
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )

    async def async_update(self):
        """Update Brother entity."""
        await self.coordinator.async_request_refresh()
