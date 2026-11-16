"""Tests of the iNELS config flow."""

from __future__ import annotations

from unittest.mock import MagicMock

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.inels_rpc.const import CONF_UNIT, DOMAIN
from pyinels.exception import ApiException

from .conftest import HOST, PORT


@pytest.mark.parametrize("host", [HOST, f"http://{HOST}", f" http://{HOST}/ "])
async def test_user_flow(hass: HomeAssistant, mock_api: MagicMock, host: str) -> None:
    """Entry is created with the bare host, http:// is optional."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: host, CONF_PORT: PORT, CONF_UNIT: "CU3"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"iNELS ({HOST})"
    assert result["data"] == {CONF_HOST: HOST, CONF_PORT: PORT, CONF_UNIT: "CU3"}
    assert result["result"].unique_id == f"{HOST}:{PORT}"


async def test_user_flow_defaults(hass: HomeAssistant, mock_api: MagicMock) -> None:
    """Port and unit have defaults."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_HOST: HOST, CONF_PORT: 8001, CONF_UNIT: "CU3"}


@pytest.mark.parametrize(
    ("side_effect", "return_value", "error"),
    [
        (OSError("refused"), None, "cannot_connect"),
        (ApiException("common_exception", "boom"), None, "cannot_connect"),
        (None, False, "cannot_connect"),
        (RuntimeError("bug"), None, "unknown"),
    ],
)
async def test_user_flow_errors(
    hass: HomeAssistant,
    mock_api: MagicMock,
    side_effect: Exception | None,
    return_value: bool | None,
    error: str,
) -> None:
    """Errors are shown and the flow recovers."""
    mock_api.ping.side_effect = side_effect
    mock_api.ping.return_value = return_value
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_PORT: PORT, CONF_UNIT: "CU3"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}

    mock_api.ping.side_effect = None
    mock_api.ping.return_value = True
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_PORT: PORT, CONF_UNIT: "CU3"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_user_flow_already_configured(
    hass: HomeAssistant, mock_api: MagicMock, mock_config_entry: MockConfigEntry
) -> None:
    """The same Connection Server cannot be added twice."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: f"http://{HOST}", CONF_PORT: PORT, CONF_UNIT: "CU3"},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    mock_api.ping.assert_not_called()


async def test_reconfigure(
    hass: HomeAssistant, mock_api: MagicMock, init_integration: MockConfigEntry
) -> None:
    """The host and port can be changed."""
    entry = init_integration
    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "http://10.0.0.5", CONF_PORT: 8002}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data == {CONF_HOST: "10.0.0.5", CONF_PORT: 8002, CONF_UNIT: "CU3"}
    assert entry.unique_id == "10.0.0.5:8002"


async def test_reconfigure_same_host(
    hass: HomeAssistant, mock_api: MagicMock, init_integration: MockConfigEntry
) -> None:
    """Reconfiguring to the same address is not a duplicate."""
    entry = init_integration
    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_PORT: PORT}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.unique_id == f"{HOST}:{PORT}"


async def test_reconfigure_cannot_connect(
    hass: HomeAssistant, mock_api: MagicMock, init_integration: MockConfigEntry
) -> None:
    """Connection is checked before the entry is changed."""
    entry = init_integration
    result = await entry.start_reconfigure_flow(hass)
    mock_api.ping.side_effect = OSError("refused")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "10.0.0.5", CONF_PORT: PORT}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
    assert entry.data[CONF_HOST] == HOST


async def test_reconfigure_to_other_entry(
    hass: HomeAssistant, mock_api: MagicMock, init_integration: MockConfigEntry
) -> None:
    """Reconfiguring to the address of another entry is refused."""
    other = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "10.0.0.5", CONF_PORT: PORT, CONF_UNIT: "CU3"},
        unique_id=f"10.0.0.5:{PORT}",
        minor_version=2,
    )
    other.add_to_hass(hass)
    result = await init_integration.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "10.0.0.5", CONF_PORT: PORT}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
