"""InelsEntity class"""
from homeassistant.helpers import entity

from .const import DOMAIN, VERSION, TITLE


class InelsEntity(entity.Entity):
    def __init__(self, coordinator, device):
        self.coordinator = coordinator
        self.device = device

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
            "suggested_area": self.device.group
        }

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            "inels_type": type(self.device).__name__,
            "inels_id": self.device.unique_id,
        }

    async def async_added_to_hass(self):
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Update Brother entity."""
        await self.coordinator.async_request_refresh()
