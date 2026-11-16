"""Data update coordinator of the iNELS integration."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pyinels.api import Api
from pyinels.device import Device

from .const import DOMAIN, PYINELS_ERRORS, UPDATE_INTERVAL

if TYPE_CHECKING:
    from . import InelsConfigEntry

_LOGGER = logging.getLogger(__name__)


def build_url(host: str) -> str:
    """Return the Connection Server url, adding http:// when missing."""
    host = host.strip().rstrip("/")
    if "://" in host:
        return host
    return f"http://{host}"


def bare_host(host: str) -> str:
    """Return the host without the scheme and the trailing slash."""
    host = host.strip().rstrip("/")
    if "://" in host:
        host = host.split("://", 1)[1]
    return host


def entry_unique_id(host: str, port: int | str) -> str:
    """Return the unique id of a config entry."""
    return f"{bare_host(host)}:{port}"


class InelsDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any] | None]):
    """Load the devices once and poll their values from the Connection Server."""

    config_entry: InelsConfigEntry

    def __init__(
        self, hass: HomeAssistant, config_entry: InelsConfigEntry, api: Api
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
            always_update=True,
        )
        self.api = api
        self.devices: list[Device] = []
        # The XML-RPC proxy of pyinels is shared and not thread safe, every
        # call to the Connection Server (reads and writes) goes through it.
        self.api_lock = asyncio.Lock()

    async def async_api_call(self, func: Callable[..., Any], *args: Any) -> Any:
        """Run a blocking pyinels call, one at a time."""
        async with self.api_lock:
            return await self.hass.async_add_executor_job(func, *args)

    async def _async_setup(self) -> None:
        """Load the list of devices published by the Connection Server."""
        try:
            self.devices = await self.async_api_call(self.api.getAllDevices)
        except PYINELS_ERRORS as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="cannot_connect",
                translation_placeholders={"error": str(err)},
            ) from err
        _LOGGER.debug("Loaded %s devices from the Connection Server", len(self.devices))

    async def _async_update_data(self) -> dict[str, Any] | None:
        """Read the values of all devices."""
        try:
            return await self.async_api_call(self.api.fetch_all_devices)
        except PYINELS_ERRORS as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_failed",
                translation_placeholders={"error": str(err)},
            ) from err
