"""Constants for inels."""
# Base component constants
NAME = "Inels"
DOMAIN = "inels"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.2.0"

ISSUE_URL = "https://github.com/JH-Soft-Technology/InelsForHass/Issues"

# Icons
ICON_SWITCH = "mdi:power-socket"
ICON_LIGHT = "mdi:lightbulb"
ICON_DOOR = "mdi:gate"
ICON_SHUTTER = "mdi:window-shutter"

# Device classes
BINARY_SENSOR_DEVICE_CLASS = "connectivity"
DEVICE_CLASS_SHUTTER = "shutter"

# Platforms
SWITCH = "switch"
LIGHT = "light"
DOOR = "door"
COVER = "cover"

PLATFORMS = [SWITCH, LIGHT, COVER]


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
