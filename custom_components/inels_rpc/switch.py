"""Switch platform of the iNELS integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from pyinels.device.pyDoor import pyDoor
from pyinels.device.pySwitch import pySwitch

from . import InelsConfigEntry
from .const import TYPE_DOOR, TYPE_SWITCH
from .entity import InelsEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: InelsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the switches and the gates."""
    coordinator = entry.runtime_data
    entities: list[InelsSwitch] = [
        InelsSwitch(coordinator, pySwitch(dev))
        for dev in coordinator.devices_of_type(TYPE_SWITCH)
    ]
    entities.extend(
        InelsDoor(coordinator, pyDoor(dev))
        for dev in coordinator.devices_of_type(TYPE_DOOR)
    )
    async_add_entities(entities)


class InelsSwitch(InelsEntity, SwitchEntity):
    """Relay or socket."""

    _attr_name = None
    _attr_translation_key = "switch"

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self._value(self.device.state)

    def _actual_value(self) -> Any:
        return self.device.state

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        await self._async_write(self.device.turn_on)
        self._set_pending(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        await self._async_write(self.device.turn_off)
        self._set_pending(False)


class InelsDoor(InelsSwitch):
    """Gate or garage door controlled by a pulse."""

    _attr_translation_key = "door"
