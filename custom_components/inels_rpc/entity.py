"""Base entity of the iNELS integration."""

from __future__ import annotations

from collections.abc import Callable
from time import monotonic
from typing import TYPE_CHECKING, Any

from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DEVICE_MODELS, DOMAIN, MANUFACTURER, PYINELS_ERRORS
from .coordinator import InelsDataUpdateCoordinator

if TYPE_CHECKING:
    from pyinels.device.pyBase import pyBase

# How long a written value is kept when the polled value does not match it yet.
# The central unit applies a write with a delay, so the first read after a
# command can still return the previous value.
PENDING_TIMEOUT = 6


class InelsEntity(CoordinatorEntity[InelsDataUpdateCoordinator]):
    """Entity backed by one device published by the Connection Server."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: InelsDataUpdateCoordinator, device: pyBase) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.device = device
        self._pending: Any = None
        self._pending_until = 0.0

        inels_type = device._device.type  # pylint: disable=protected-access
        self._attr_unique_id = device.unique_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.unique_id)},
            name=device.name,
            manufacturer=MANUFACTURER,
            model=DEVICE_MODELS.get(inels_type, inels_type),
            suggested_area=device.group,
        )
        self._attr_extra_state_attributes = {
            "inels_type": type(device).__name__,
            "inels_id": device.unique_id,
        }

    def _set_pending(self, value: Any, timeout: float = PENDING_TIMEOUT) -> None:
        """Remember the value written by a command and show it right away."""
        self._pending = value
        self._pending_until = monotonic() + timeout
        self.async_write_ha_state()

    def _actual_value(self) -> Any:
        """Value compared with the pending one; overridden by the platforms."""
        return None

    def _value(self, actual: Any) -> Any:
        """Return the pending value while the unit has not confirmed it yet."""
        if self._pending is None:
            return actual
        if monotonic() > self._pending_until:
            self._pending = None
            return actual
        return self._pending

    @callback
    def _handle_coordinator_update(self) -> None:
        """Drop the pending value once a poll confirms it, then write state.

        Only a poll can confirm the value: pyinels stores the written value
        in the device right after the write, before the unit applies it."""
        if self._pending is not None and self._actual_value() == self._pending:
            self._pending = None
        self._value(self._actual_value())
        self.async_write_ha_state()

    async def _async_write(self, func: Callable[..., Any], *args: Any) -> None:
        """Write to the central unit, translating library errors."""
        try:
            await self.coordinator.async_api_call(func, *args)
        except PYINELS_ERRORS as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="write_failed",
                translation_placeholders={
                    "name": self.device.name,
                    "error": str(err),
                },
            ) from err
