"""Constants for inels."""
# Base component constants
NAME = "Inels"
DOMAIN = "inels"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.1"

ISSUE_URL = "https://github.com/JH-Soft-Technology/InelsForHass/Issues"

# Icons
ICON = "mdi:format-quote-close"

# Device classes
BINARY_SENSOR_DEVICE_CLASS = "connectivity"

# Platforms
BINARY_SENSOR = "binary_sensor"
SENSOR = "sensor"
SWITCH = "switch"
PLATFORMS = [SWITCH]


# Configuration and options
CONF_ENABLED = "enabled"
CONF_HOST = "host"
CONF_PORT = "port"
CONF_VERSION = "version"

# Defaults
DEFAULT_NAME = DOMAIN


STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
