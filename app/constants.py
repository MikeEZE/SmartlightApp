"""
Constants used throughout the application
"""

import logging
import os
from pathlib import Path

# Application information
APP_NAME = "Smart Light Controller"
APP_VERSION = "1.0.0"

# Paths
APP_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = Path.home() / '.smart_light_controller'
CONFIG_FILE = CONFIG_DIR / 'config.json'

# Ensure config directory exists
CONFIG_DIR.mkdir(exist_ok=True)

# Logging configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = logging.INFO

# UI Constants
UI_REFRESH_RATE = 500  # milliseconds
DEFAULT_WINDOW_WIDTH = 900
DEFAULT_WINDOW_HEIGHT = 600

# Light control
DEFAULT_BRIGHTNESS = 100  # percentage
DEFAULT_COLOR_TEMP = 4000  # Kelvin
MIN_COLOR_TEMP = 2000  # Kelvin
MAX_COLOR_TEMP = 6500  # Kelvin
HUE_RANGE = (0, 65535)
SATURATION_RANGE = (0, 254)
BRIGHTNESS_RANGE = (0, 254)

# Network settings
DISCOVERY_TIMEOUT = 5  # seconds
NETWORK_TIMEOUT = 3    # seconds
HUE_BRIDGE_DISCOVERY_URL = "https://discovery.meethue.com/"

# Common light attributes
ATTR_BRIGHTNESS = "brightness"
ATTR_COLOR_TEMP = "color_temp"
ATTR_HUE = "hue"
ATTR_SATURATION = "saturation"
ATTR_RGB_COLOR = "rgb_color"
ATTR_POWER = "power"
ATTR_NAME = "name"
ATTR_ID = "id"
ATTR_MODEL = "model"
ATTR_MANUFACTURER = "manufacturer"
ATTR_TYPE = "type"
ATTR_STATE = "state"
ATTR_REACHABLE = "reachable"
ATTR_PRODUCT_ID = "product_id"
ATTR_FIRMWARE = "firmware"

# Light protocols
PROTOCOL_HUE = "hue"
PROTOCOL_LIFX = "lifx"

# All supported protocols
SUPPORTED_PROTOCOLS = [PROTOCOL_HUE, PROTOCOL_LIFX]

# Default light states
STATE_ON = "on"
STATE_OFF = "off"
STATE_UNREACHABLE = "unreachable"
STATE_UNKNOWN = "unknown"
