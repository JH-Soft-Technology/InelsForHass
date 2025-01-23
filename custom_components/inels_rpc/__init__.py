"""The inels integration."""
from __future__ import annotations
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from pyinels.api import Api
from .const import (
    DOMAIN,
    HOST_STR,
    PLATFORMS,
    PORT_STR,
    STARTUP_MESSAGE,
    UNIT_STR,
    DOMAIN_DATA,
)

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=5)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up inels from a config entry."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    host = entry.data.get(HOST_STR)
    port = entry.data.get(PORT_STR)
    unit = entry.data.get(UNIT_STR)

    _LOGGER.info("Creating iNels coordinator")

    coordinator = InelsDataUpdateCoordinator(hass, host=host, port=port, unit=unit)
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = coordinator
    hass.data[DOMAIN][DOMAIN_DATA] = await hass.async_add_executor_job(
        coordinator.api.getAllDevices
    )

    _LOGGER.info("Loading platforms with entries")
    _LOGGER.info(entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


class InelsDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, host, port, unit):
        """Initialize."""
        self.api = Api(host, str(port), unit)
        self.hass = hass
        self.platforms = []

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            await self.hass.async_add_executor_job(self.api.fetch_all_devices)
            return None
            return None
        except Exception as exception:
            raise UpdateFailed(exception)
