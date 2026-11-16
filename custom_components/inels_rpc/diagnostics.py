"""Diagnostics of the iNELS integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from . import InelsConfigEntry

TO_REDACT = {CONF_HOST, "unique_id", "title"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: InelsConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "last_update_success": coordinator.last_update_success,
        "devices": [
            {
                "type": dev.type,
                "id": dev.id,
                "name": dev.title,
                "group": dev.group,
                "value": dev.value,
            }
            for dev in coordinator.devices
        ],
    }
