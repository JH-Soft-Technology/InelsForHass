"""Fixtures of the iNELS integration tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
import pyinels.api  # noqa: F401  # pyinels.device needs pyinels.api imported first
from pyinels.device import Device
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.inels_rpc.const import CONF_UNIT, DOMAIN

HOST = "192.168.1.10"
PORT = 8001


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations in every test."""
    return


def _device(api: MagicMock, json: dict, value: dict) -> Device:
    """Create a pyinels device with a value as read from the server."""
    device = Device(json, api)
    device.set_value(value)
    return device


def make_devices(api: MagicMock) -> list[Device]:
    """Devices published by the mocked Connection Server."""
    return [
        _device(
            api,
            {"inels": "Light_1", "name": "Kitchen", "type": "light", "group": "Ground"},
            {"Light_1": "1"},
        ),
        _device(
            api,
            {"inels": "Dimmer_1", "name": "Hall", "type": "light", "group": "Ground"},
            {"Dimmer_1": "50.0"},
        ),
        _device(
            api,
            {"inels": "Socket_1", "name": "Socket", "type": "switch", "group": "Attic"},
            {"Socket_1": "0"},
        ),
        _device(
            api,
            {"inels": "Gate_1", "name": "Gate", "type": "door", "group": "Garden"},
            {"Gate_1": "0"},
        ),
        _device(
            api,
            {
                "inels": "Sh_up_Sh_down",
                "up": "Sh_up",
                "down": "Sh_down",
                "name": "Blind",
                "type": "shutter",
                "group": "Ground",
            },
            {"Sh_up": 0, "Sh_down": 0},
        ),
        _device(
            api,
            {
                "inels": "Obyvak_Temperature",
                "therm": "Obyvak_Temperature",
                "stateth": "Obyvak_StateTH",
                "name": "Living room",
                "type": "therm",
                "group": "Ground",
            },
            {
                "Obyvak_Temperature": "21.5",
                "Obyvak_StateTH": "22.0",
                "Obyvak_StateM": "0",
                "Obyvak_StateU": "0",
                "Obyvak_StateN": "1",
                "Obyvak_StateK": "0",
            },
        ),
        _device(
            api,
            {"inels": "Air_1", "name": "Airing", "type": "airing", "group": "Ground"},
            {"Air_1": "0"},
        ),
    ]


@pytest.fixture
def mock_api() -> Generator[MagicMock]:
    """Mock the pyinels Api used by the integration and the config flow."""
    api = MagicMock()
    api.ping.return_value = True
    api.getAllDevices.return_value = make_devices(api)
    api.fetch_all_devices.return_value = {}
    with (
        patch("custom_components.inels_rpc.Api", return_value=api),
        patch("custom_components.inels_rpc.config_flow.Api", return_value=api),
    ):
        yield api


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Config entry as created by the 0.5.0 config flow."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=f"iNELS ({HOST})",
        data={CONF_HOST: HOST, CONF_PORT: PORT, CONF_UNIT: "CU3"},
        unique_id=f"{HOST}:{PORT}",
        version=1,
        minor_version=2,
    )


@pytest.fixture
async def init_integration(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_api: MagicMock
) -> MockConfigEntry:
    """Set up the integration."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry
