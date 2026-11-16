"""Tests of the iNELS integration setup."""

from __future__ import annotations

from unittest.mock import MagicMock

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_PORT, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.inels_rpc import async_remove_config_entry_device
from custom_components.inels_rpc.const import CONF_UNIT, DOMAIN
from pyinels.exception import ApiException

from .conftest import HOST, PORT


async def test_setup_and_unload(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_api: MagicMock
) -> None:
    """Entry is set up with one device load and one read, then unloaded."""
    entry = init_integration
    assert entry.state is ConfigEntryState.LOADED
    assert mock_api.getAllDevices.call_count == 1
    assert mock_api.fetch_all_devices.call_count == 1
    assert len(hass.states.async_entity_ids(DOMAIN)) == 0
    assert (
        len(er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)) == 7
    )

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_not_ready_devices(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_api: MagicMock
) -> None:
    """Setup is retried when the device list cannot be loaded."""
    mock_api.getAllDevices.side_effect = OSError("refused")
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_setup_not_ready_values(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_api: MagicMock
) -> None:
    """Setup is retried when the values cannot be read."""
    mock_api.fetch_all_devices.side_effect = ApiException("read", "boom")
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_update_failed(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_api: MagicMock
) -> None:
    """Entities become unavailable when the server stops answering."""
    assert hass.states.get("switch.socket").state == "off"
    mock_api.fetch_all_devices.side_effect = OSError("timeout")
    await init_integration.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get("switch.socket").state == STATE_UNAVAILABLE

    mock_api.fetch_all_devices.side_effect = None
    await init_integration.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get("switch.socket").state == "off"


async def test_device_info(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Devices carry the iNELS name, type and room."""
    device = dr.async_get(hass).async_get_device(
        identifiers={(DOMAIN, "Obyvak_Temperature")}
    )
    assert device.name == "Living room"
    assert device.manufacturer == "ELKO EP"
    assert device.model == "heat-control"
    assert device.sw_version is None
    assert device.suggested_area == "Ground"


async def test_migrate_0_4_entry(hass: HomeAssistant, mock_api: MagicMock) -> None:
    """A 0.4.x entry gets the unique id, the data are not touched."""
    data = {CONF_HOST: f"http://{HOST}", CONF_PORT: PORT, CONF_UNIT: "CU3"}
    entry = MockConfigEntry(domain=DOMAIN, title="iNELS", data=data, version=1)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert entry.unique_id == f"{HOST}:{PORT}"
    assert entry.minor_version == 2
    assert entry.data == data
    assert entry.title == "iNELS"


async def test_migrate_duplicate(hass: HomeAssistant, mock_api: MagicMock) -> None:
    """Unique id is not set when another entry already uses it."""
    MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: HOST, CONF_PORT: PORT, CONF_UNIT: "CU3"},
        unique_id=f"{HOST}:{PORT}",
        minor_version=2,
    ).add_to_hass(hass)
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: f"http://{HOST}", CONF_PORT: PORT, CONF_UNIT: "CU3"},
        version=1,
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.unique_id is None
    assert entry.minor_version == 2


async def test_migrate_future_version(hass: HomeAssistant, mock_api: MagicMock) -> None:
    """Entries of a newer version are not loaded."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: HOST, CONF_PORT: PORT, CONF_UNIT: "CU3"},
        version=2,
    )
    entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.MIGRATION_ERROR


async def test_stale_devices_removed(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_api: MagicMock
) -> None:
    """Devices which are not published anymore are removed on setup."""
    mock_config_entry.add_to_hass(hass)
    device_registry = dr.async_get(hass)
    stale = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        identifiers={(DOMAIN, "Removed_1")},
        name="Removed",
    )
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert device_registry.async_get(stale.id) is None
    assert device_registry.async_get_device(identifiers={(DOMAIN, "Light_1")})


async def test_stale_devices_kept_on_empty_list(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_api: MagicMock
) -> None:
    """An empty device list never wipes the registry."""
    mock_api.getAllDevices.return_value = []
    mock_config_entry.add_to_hass(hass)
    device_registry = dr.async_get(hass)
    kept = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        identifiers={(DOMAIN, "Light_1")},
        name="Kitchen",
    )
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert device_registry.async_get(kept.id)


async def test_remove_config_entry_device(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Only devices not published by the server can be removed by the user."""
    device_registry = dr.async_get(hass)
    current = device_registry.async_get_device(identifiers={(DOMAIN, "Light_1")})
    assert not await async_remove_config_entry_device(hass, init_integration, current)

    stale = device_registry.async_get_or_create(
        config_entry_id=init_integration.entry_id,
        identifiers={(DOMAIN, "Removed_1")},
    )
    assert await async_remove_config_entry_device(hass, init_integration, stale)
