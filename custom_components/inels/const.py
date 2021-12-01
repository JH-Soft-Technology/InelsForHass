"""Constants for the inels integration."""

DOMAIN = "inels"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.3.2"

ISSUE_URL = "https://github.com/JH-Soft-Technology/InelsForHass/Issues"

TITLE = "iNELS"
HOST_STR = "host"
PORT_STR = "port"
UNIT_STR = "unit"
USER_STR = "user"
TITLE_STR = "title"

ERROR_BASE = "base"
ERROR_BASE_CANNOT_CONNECT = "cannot_connect"
ERROR_BASE_INVALID_AUTH = "invalid_auth"
ERROR_BASE_UNKNOWN = "unknown"

# Icons
ICON_SWITCH = "mdi:power-socket"
ICON_LIGHT = "mdi:lightbulb"
ICON_DOOR = "mdi:gate"
ICON_SHUTTER = "mdi:window-shutter"

PLATFORM_SWITCH = "switch"
PLATFORM_LIGHT = "light"
PLATFORM_COVER = "cover"
PLATFORM_DOOR = "door"

PLATFORMS = [PLATFORM_SWITCH, PLATFORM_LIGHT, PLATFORM_COVER]

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{TITLE}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
