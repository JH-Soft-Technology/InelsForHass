"""Sensor platform for inels."""

import logging

from pyinels.device.pyTherm import pyTherm

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature

from custom_components.inels_rpc.entity import InelsEntity
from custom_components.inels_rpc.const import (
    DOMAIN,
    DOMAIN_DATA,
    PLATFORM_THERM,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""

    _LOGGER.info("Setting up temperature sensors")

    devices = hass.data[DOMAIN][DOMAIN_DATA]
    coordinator = hass.data[DOMAIN][entry.entry_id]

    therms = [
        await hass.async_add_executor_job(pyTherm, dev)
        for dev in devices
        if dev.type == PLATFORM_THERM
    ]

    await coordinator.async_refresh()

    if len(therms) > 0:
        async_add_devices(
            [InelsTemperatureSensor(coordinator, therm) for therm in therms],
            True,
        )


class InelsTemperatureSensor(InelsEntity, SensorEntity):
    """Room temperature measured by the heat control."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self.device.name} temperature"

    @property
    def native_value(self):
        """Return the measured temperature."""
        return self.device.current_temperature
