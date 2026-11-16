"""Constants for the iNELS integration."""

from datetime import timedelta
from xmlrpc.client import Error as XmlRpcError

from homeassistant.const import Platform
from pyinels.exception import ApiException

DOMAIN = "inels_rpc"
VERSION = "0.5.0"

TITLE = "iNELS"
MANUFACTURER = "ELKO EP"

CONF_UNIT = "unit"

DEFAULT_PORT = 8001
DEFAULT_UNIT = "CU3"

UPDATE_INTERVAL = timedelta(seconds=5)

# Errors raised by pyinels and the underlying XML-RPC client when the
# Connection Server cannot be reached or returns unexpected data.
PYINELS_ERRORS = (ApiException, OSError, XmlRpcError, KeyError, ValueError)

# Device types as recognised by pyinels
TYPE_LIGHT = "light"
TYPE_SWITCH = "switch"
TYPE_DOOR = "door"
TYPE_SHUTTER = "shutter"
TYPE_THERM = "therm"

# Model shown in the device registry for every pyinels device type
DEVICE_MODELS = {
    TYPE_LIGHT: "light",
    TYPE_SWITCH: "switch",
    TYPE_DOOR: "door",
    TYPE_SHUTTER: "shutter",
    TYPE_THERM: "heat-control",
}

PLATFORMS = [
    Platform.CLIMATE,
    Platform.COVER,
    Platform.LIGHT,
    Platform.SENSOR,
    Platform.SWITCH,
]
