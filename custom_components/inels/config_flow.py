"""Adds config flow for Inels."""
import logging
import voluptuous as vol
import async_timeout
from homeassistant import config_entries
from homeassistant.core import callback

from pyinels.api import Api

from custom_components.inels.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_VERSION,
    DOMAIN,
    NAME,
    PLATFORMS,
)

_LOGGER = logging.getLogger(__name__)


class InelsFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Inels."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    _LOGGER.info("Config flow for Inels")

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(
        self, user_input=None  # pylint: disable=bad-continuation
    ):
        """Handle a flow initialized by the user."""
        self._errors = {}

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            valid = await self._test_credentials(
                user_input[CONF_HOST], user_input[CONF_PORT], user_input[CONF_VERSION]
            )
            if valid:
                return self.async_create_entry(title=NAME, data=user_input)
            else:
                self._errors["base"] = "auth"

            return await self._show_config_form(user_input)

        return await self._show_config_form(user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return InelsOptionsFlowHandler(config_entry)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT): str,
                    vol.Required(CONF_VERSION): str,
                }
            ),
            errors=self._errors,
        )

    async def _test_credentials(self, host, port, version):
        """Return true if credentials is valid."""
        try:
            with async_timeout.timeout(5):
                _LOGGER.info("Testing connection")
                api = Api(host, str(port), version)

                if not api.ping():
                    raise Exception("not_available")

            return True
        except Exception as ex:  # pylint: disable=broad-except
            print(ex)
            pass
        return False


class InelsOptionsFlowHandler(config_entries.OptionsFlow):
    """Inels config flow options handler."""

    def __init__(self, config_entry):
        """Initialize HACS options flow."""
        _LOGGER.info("Initialize InelsOptionsFlowHandler")

        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(x, default=self.options.get(x, True)): bool
                    for x in sorted(PLATFORMS)
                }
            ),
        )

    async def _update_options(self):
        """Update config entry options."""
        return self.async_create_entry(
            title=self.config_entry.data.get(NAME), data=self.options
        )
