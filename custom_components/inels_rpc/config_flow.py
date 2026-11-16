"""Config flow of the iNELS integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.exceptions import HomeAssistantError
import voluptuous as vol
from pyinels.api import Api

from .const import (
    CONF_UNIT,
    DEFAULT_PORT,
    DEFAULT_UNIT,
    DOMAIN,
    PYINELS_ERRORS,
    TITLE,
)
from .coordinator import bare_host, build_url, entry_unique_id

_LOGGER = logging.getLogger(__name__)

DESCRIPTION_PLACEHOLDERS = {
    "docs_url": "https://github.com/JH-Soft-Technology/InelsForHass"
}

PORT_VALIDATOR = vol.All(vol.Coerce(int), vol.Range(min=1, max=65535))


def _user_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_HOST, default=defaults.get(CONF_HOST, vol.UNDEFINED)
            ): str,
            vol.Required(
                CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)
            ): PORT_VALIDATOR,
            vol.Required(CONF_UNIT, default=defaults.get(CONF_UNIT, DEFAULT_UNIT)): str,
        }
    )


def _reconfigure_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=defaults[CONF_HOST]): str,
            vol.Required(CONF_PORT, default=defaults[CONF_PORT]): PORT_VALIDATOR,
        }
    )


async def _async_validate(flow: ConfigFlow, host: str, port: int) -> dict[str, str]:
    """Ping the Connection Server, return the form errors."""
    api = Api(build_url(host), str(port), DEFAULT_UNIT)
    try:
        if not await flow.hass.async_add_executor_job(api.ping):
            raise CannotConnect
    except (CannotConnect, *PYINELS_ERRORS):
        return {"base": "cannot_connect"}
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("Unexpected exception")
        return {"base": "unknown"}
    return {}


class InelsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for iNELS."""

    VERSION = 1
    MINOR_VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = bare_host(user_input[CONF_HOST])
            port = user_input[CONF_PORT]
            await self.async_set_unique_id(entry_unique_id(host, port))
            self._abort_if_unique_id_configured()

            errors = await _async_validate(self, host, port)
            if not errors:
                return self.async_create_entry(
                    title=f"{TITLE} ({host})",
                    data={**user_input, CONF_HOST: host},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_user_schema(user_input or {}),
            errors=errors,
            description_placeholders=DESCRIPTION_PLACEHOLDERS,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change the address of the Connection Server."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            host = bare_host(user_input[CONF_HOST])
            port = user_input[CONF_PORT]
            unique_id = entry_unique_id(host, port)
            if unique_id != entry.unique_id:
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

            errors = await _async_validate(self, host, port)
            if not errors:
                return self.async_update_reload_and_abort(
                    entry,
                    unique_id=unique_id,
                    data_updates={CONF_HOST: host, CONF_PORT: port},
                )

        defaults = user_input or {
            CONF_HOST: bare_host(entry.data[CONF_HOST]),
            CONF_PORT: entry.data[CONF_PORT],
        }
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_reconfigure_schema(defaults),
            errors=errors,
            description_placeholders=DESCRIPTION_PLACEHOLDERS,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
