"""Config flow for inels integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from pyinels.api import Api

from .const import (
    DOMAIN,
    HOST_STR,
    PORT_STR,
    TITLE,
    UNIT_STR,
    USER_STR,
    TITLE_STR,
    ERROR_BASE_INVALID_AUTH,
    ERROR_BASE,
    ERROR_BASE_CANNOT_CONNECT,
    ERROR_BASE_UNKNOWN,
)

_LOGGER = logging.getLogger(__name__)


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(HOST_STR): str,
        vol.Required(PORT_STR): int,
        vol.Required(UNIT_STR): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""

    api = Api(data[HOST_STR], data[PORT_STR], data[UNIT_STR])

    # when PyPI library has no async methods then is neccessary to wrapp them into
    # the hass.async_add_executor_job(func, param1[x], param2[y])
    ping = await hass.async_add_executor_job(api.ping)

    if ping == False:
        raise CannotConnect

    # Return info that you want to store in the config entry.
    return {TITLE_STR: TITLE, "Data": data}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for inels."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id=USER_STR, data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors[ERROR_BASE] = ERROR_BASE_CANNOT_CONNECT
        except InvalidAuth:
            errors[ERROR_BASE] = ERROR_BASE_INVALID_AUTH
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors[ERROR_BASE] = ERROR_BASE_UNKNOWN
        else:
            return self.async_create_entry(title=info[TITLE_STR], data=user_input)

        return self.async_show_form(
            step_id=USER_STR, data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
