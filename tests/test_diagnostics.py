"""Tests of the iNELS diagnostics."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.inels_rpc.diagnostics import async_get_config_entry_diagnostics

from .conftest import HOST


async def test_diagnostics(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Diagnostics contain the devices and no address of the server."""
    result = await async_get_config_entry_diagnostics(hass, init_integration)

    assert HOST not in str(result)
    assert result["entry"]["data"]["host"] == "**REDACTED**"
    assert result["entry"]["data"]["port"] == 8001
    assert result["last_update_success"] is True
    assert len(result["devices"]) == 7
    assert result["devices"][0] == {
        "type": "light",
        "id": "Light_1",
        "name": "Kitchen",
        "group": "Ground",
        "value": {"Light_1": "1"},
    }
