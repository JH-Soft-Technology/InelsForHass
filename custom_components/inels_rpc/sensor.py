"""Sensor platform of the iNELS integration."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from pyinels.device.pyTherm import pyTherm

from . import InelsConfigEntry
from .const import TYPE_THERM
from .entity import InelsEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: InelsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the room temperature sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        InelsTemperatureSensor(coordinator, pyTherm(dev))
        for dev in coordinator.devices
        if dev.type == TYPE_THERM
    )


class InelsTemperatureSensor(InelsEntity, SensorEntity):
    """Room temperature measured by the heat control."""

    _attr_translation_key = "room_temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    device: pyTherm

    @property
    def native_value(self) -> float | None:
        """Return the measured temperature."""
        return self.device.current_temperature
