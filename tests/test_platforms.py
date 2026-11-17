"""Tests of the iNELS entity platforms."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from homeassistant.components.climate import (
    ATTR_PRESET_MODE,
    ATTR_PRESET_MODES,
    DOMAIN as CLIMATE_DOMAIN,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_PRESET_MODE,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.cover import (
    DOMAIN as COVER_DOMAIN,
    CoverEntityFeature,
)
from homeassistant.components.light import ATTR_BRIGHTNESS, DOMAIN as LIGHT_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_SUPPORTED_FEATURES,
    SERVICE_CLOSE_COVER,
    SERVICE_OPEN_COVER,
    SERVICE_STOP_COVER,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from pyinels.exception import ApiException


def _device(entry: MockConfigEntry, unique_id: str):
    return next(dev for dev in entry.runtime_data.devices if dev.id == unique_id)


async def _refresh(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()


def _written(mock_api: MagicMock) -> dict:
    """Value of the last write to the central unit."""
    return mock_api.write.call_args.args[1]


async def test_entities(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Entities keep the unique ids of 0.4.x and use the device names."""
    registry = er.async_get(hass)
    expected = {
        "light.kitchen": "Light_1",
        "light.hall": "Dimmer_1",
        "switch.socket": "Socket_1",
        "switch.gate": "Gate_1",
        "cover.blind": "Sh_up_Sh_down",
        "climate.living_room": "Obyvak_Temperature",
        "sensor.living_room_room_temperature": "Obyvak_Temperature",
    }
    for entity_id, unique_id in expected.items():
        assert registry.async_get(entity_id).unique_id == unique_id

    state = hass.states.get("light.kitchen")
    assert state.attributes[ATTR_FRIENDLY_NAME] == "Kitchen"
    assert state.attributes["inels_type"] == "pyLight"
    assert state.attributes["inels_id"] == "Light_1"
    assert (
        hass.states.get("sensor.living_room_room_temperature").attributes[
            ATTR_FRIENDLY_NAME
        ]
        == "Living room Room temperature"
    )


async def test_light(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_api: MagicMock
) -> None:
    """On/off light."""
    assert hass.states.get("light.kitchen").state == STATE_ON

    await hass.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: "light.kitchen"}, blocking=True
    )
    assert _written(mock_api) == {"Light_1": "0"}
    assert hass.states.get("light.kitchen").state == STATE_OFF

    await hass.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: "light.kitchen"}, blocking=True
    )
    assert _written(mock_api) == {"Light_1": "1"}
    assert hass.states.get("light.kitchen").state == STATE_ON


async def test_light_dimmable(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_api: MagicMock
) -> None:
    """Dimmable light converts the brightness between 0-255 and 0-100."""
    state = hass.states.get("light.hall")
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 128

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "light.hall", ATTR_BRIGHTNESS: 255},
        blocking=True,
    )
    assert _written(mock_api) == {"Dimmer_1": "100.0"}
    assert hass.states.get("light.hall").attributes[ATTR_BRIGHTNESS] == 255

    await hass.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: "light.hall"}, blocking=True
    )
    assert _written(mock_api) == {"Dimmer_1": "0.0"}
    assert hass.states.get("light.hall").state == STATE_OFF

    await hass.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: "light.hall"}, blocking=True
    )
    assert _written(mock_api) == {"Dimmer_1": "100.0"}
    assert hass.states.get("light.hall").state == STATE_ON


async def test_pending_value(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_api: MagicMock
) -> None:
    """The commanded state is kept until confirmed or expired (0.4.3 fix)."""
    now = 1000.0
    with patch("custom_components.inels_rpc.entity.monotonic", side_effect=lambda: now):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.socket"},
            blocking=True,
        )
        assert hass.states.get("switch.socket").state == STATE_ON

        # the central unit has not applied the write yet
        _device(init_integration, "Socket_1").set_value({"Socket_1": "0"})
        now += 3
        await _refresh(hass, init_integration)
        assert hass.states.get("switch.socket").state == STATE_ON

        # the pending value expires
        now += 4
        await _refresh(hass, init_integration)
        assert hass.states.get("switch.socket").state == STATE_OFF

        # a confirmed value drops the pending one right away
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.socket"},
            blocking=True,
        )
        await _refresh(hass, init_integration)
        _device(init_integration, "Socket_1").set_value({"Socket_1": "0"})
        await _refresh(hass, init_integration)
        assert hass.states.get("switch.socket").state == STATE_OFF


async def test_switch(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_api: MagicMock
) -> None:
    """Relay switching."""
    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: "switch.socket"}, blocking=True
    )
    assert _written(mock_api) == {"Socket_1": "1"}
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "switch.socket"},
        blocking=True,
    )
    assert _written(mock_api) == {"Socket_1": "0"}
    assert hass.states.get("switch.socket").state == STATE_OFF


async def test_door(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_api: MagicMock
) -> None:
    """Gate is triggered by a pulse."""
    with patch("pyinels.device.pyDoor.sleep"):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.gate"},
            blocking=True,
        )
    assert [call.args[1] for call in mock_api.write.call_args_list] == [
        {"Gate_1": "1"},
        {"Gate_1": "0"},
    ]
    assert hass.states.get("switch.gate").state == STATE_ON


async def test_cover(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_api: MagicMock
) -> None:
    """Shutter supports open, close and stop only."""
    state = hass.states.get("cover.blind")
    assert state.state == "open"
    assert state.attributes["device_class"] == "shutter"
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
    )
    assert "current_position" not in state.attributes
    # Position is unknown, so open and close must both stay available.
    assert state.attributes["assumed_state"] is True

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: "cover.blind"},
        blocking=True,
    )
    assert _written(mock_api) == {"Sh_down": 1, "Sh_up": 0}
    assert hass.states.get("cover.blind").state == "closing"

    await hass.services.async_call(
        COVER_DOMAIN, SERVICE_STOP_COVER, {ATTR_ENTITY_ID: "cover.blind"}, blocking=True
    )
    assert _written(mock_api) == {"Sh_down": 0, "Sh_up": 0}
    assert hass.states.get("cover.blind").state == "closed"

    await hass.services.async_call(
        COVER_DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: "cover.blind"}, blocking=True
    )
    assert _written(mock_api) == {"Sh_down": 0, "Sh_up": 1}
    assert hass.states.get("cover.blind").state == "opening"


async def test_climate(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_api: MagicMock
) -> None:
    """Heat control is controlled by the levels."""
    state = hass.states.get("climate.living_room")
    assert state.state == HVACMode.HEAT
    assert state.attributes["current_temperature"] == 21.5
    assert state.attributes[ATTR_PRESET_MODE] == "normal"
    assert state.attributes[ATTR_PRESET_MODES] == [
        "minimum",
        "attenuation",
        "normal",
        "comfort",
    ]
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == ClimateEntityFeature.PRESET_MODE

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: "climate.living_room", ATTR_PRESET_MODE: "comfort"},
        blocking=True,
    )
    assert _written(mock_api) == {"Obyvak_VK": "1"}
    assert (
        hass.states.get("climate.living_room").attributes[ATTR_PRESET_MODE] == "comfort"
    )

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: "climate.living_room", "hvac_mode": HVACMode.HEAT},
        blocking=True,
    )


async def test_climate_without_levels(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Without exported levels only the temperatures are read."""
    device = _device(init_integration, "Obyvak_Temperature")
    device._ApiResource__levels_exported = False  # pylint: disable=protected-access
    await _refresh(hass, init_integration)
    state = hass.states.get("climate.living_room")
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0
    assert ATTR_PRESET_MODES not in state.attributes


async def test_sensor(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Room temperature sensor."""
    state = hass.states.get("sensor.living_room_room_temperature")
    assert state.state == "21.5"
    assert state.attributes["unit_of_measurement"] == "°C"
    assert state.attributes["device_class"] == "temperature"

    _device(init_integration, "Obyvak_Temperature").set_value(
        {"Obyvak_Temperature": "20.0", "Obyvak_StateTH": "22.0"}
    )
    await _refresh(hass, init_integration)
    assert hass.states.get("sensor.living_room_room_temperature").state == "20.0"


@pytest.mark.parametrize(
    ("domain", "service", "entity_id", "data"),
    [
        (LIGHT_DOMAIN, SERVICE_TURN_ON, "light.kitchen", {}),
        (LIGHT_DOMAIN, SERVICE_TURN_OFF, "light.hall", {}),
        (LIGHT_DOMAIN, SERVICE_TURN_ON, "light.hall", {ATTR_BRIGHTNESS: 100}),
        (SWITCH_DOMAIN, SERVICE_TURN_OFF, "switch.socket", {}),
        (COVER_DOMAIN, SERVICE_OPEN_COVER, "cover.blind", {}),
        (COVER_DOMAIN, SERVICE_CLOSE_COVER, "cover.blind", {}),
        (COVER_DOMAIN, SERVICE_STOP_COVER, "cover.blind", {}),
        (
            CLIMATE_DOMAIN,
            SERVICE_SET_PRESET_MODE,
            "climate.living_room",
            {ATTR_PRESET_MODE: "minimum"},
        ),
    ],
)
async def test_write_failed(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_api: MagicMock,
    domain: str,
    service: str,
    entity_id: str,
    data: dict,
) -> None:
    """Write errors are raised as translated Home Assistant errors."""
    before = hass.states.get(entity_id)
    mock_api.write.side_effect = ApiException("write_proxy", "connection refused")
    with pytest.raises(HomeAssistantError) as err:
        await hass.services.async_call(
            domain, service, {ATTR_ENTITY_ID: entity_id, **data}, blocking=True
        )
    assert err.value.translation_domain == "inels_rpc"
    assert err.value.translation_key == "write_failed"
    assert hass.states.get(entity_id).state == before.state


async def test_device_without_value_skipped(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_api: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A device whose variable is not published is skipped on setup."""
    devices = mock_api.getAllDevices.return_value
    next(dev for dev in devices if dev.id == "Light_1").set_value(None)
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("light.kitchen") is None
    assert hass.states.get("light.hall").state == STATE_ON
    assert "Skipping Kitchen (Light_1)" in caplog.text


async def test_device_loses_value(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """A device whose variable disappears becomes unavailable."""
    _device(init_integration, "Socket_1").set_value(None)
    await _refresh(hass, init_integration)
    assert hass.states.get("switch.socket").state == "unavailable"
    assert hass.states.get("light.kitchen").state == STATE_ON
