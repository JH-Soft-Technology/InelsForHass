"""The iNELS integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pyinels.api import Api

from .const import CONF_UNIT, DEFAULT_UNIT, DOMAIN, PLATFORMS
from .coordinator import InelsDataUpdateCoordinator, build_url, entry_unique_id

_LOGGER = logging.getLogger(__name__)

type InelsConfigEntry = ConfigEntry[InelsDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: InelsConfigEntry) -> bool:
    """Set up iNELS from a config entry."""
    api = Api(
        build_url(entry.data[CONF_HOST]),
        str(entry.data[CONF_PORT]),
        entry.data.get(CONF_UNIT, DEFAULT_UNIT),
    )
    coordinator = InelsDataUpdateCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    _async_remove_stale_devices(hass, entry, coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: InelsConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate an old config entry."""
    if entry.version > 1:
        # downgrade from a future version
        return False

    if entry.minor_version < 2:
        # 0.4.x entries have no unique id; the data are left untouched
        # so the entities and the device registry stay as they are.
        unique_id = entry.unique_id
        if unique_id is None:
            candidate = entry_unique_id(entry.data[CONF_HOST], entry.data[CONF_PORT])
            if hass.config_entries.async_entry_for_domain_unique_id(DOMAIN, candidate):
                _LOGGER.warning(
                    "Another iNELS entry already uses %s, unique id not set for %s",
                    candidate,
                    entry.title,
                )
            else:
                unique_id = candidate
        hass.config_entries.async_update_entry(
            entry, unique_id=unique_id, minor_version=2
        )

    return True


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: InelsConfigEntry, device: dr.DeviceEntry
) -> bool:
    """Allow removing a device which the Connection Server does not publish."""
    current = {dev.id for dev in entry.runtime_data.devices}
    return not any(
        identifier[0] == DOMAIN and identifier[1] in current
        for identifier in device.identifiers
    )


def _async_remove_stale_devices(
    hass: HomeAssistant,
    entry: InelsConfigEntry,
    coordinator: InelsDataUpdateCoordinator,
) -> None:
    """Remove devices which the Connection Server does not publish anymore."""
    current = {dev.id for dev in coordinator.devices}
    if not current:
        # never wipe the registry because of an empty answer
        return

    device_registry = dr.async_get(hass)
    for device in dr.async_entries_for_config_entry(device_registry, entry.entry_id):
        ids = {ident[1] for ident in device.identifiers if ident[0] == DOMAIN}
        if ids and not ids & current:
            _LOGGER.debug("Removing stale device %s", device.name)
            device_registry.async_update_device(
                device.id, remove_config_entry_id=entry.entry_id
            )
