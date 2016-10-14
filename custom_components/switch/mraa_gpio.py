"""
Allows to configure a switch using mraa GPIO.
"""
import logging

import homeassistant.helpers.config_validation as cv
import mraa
import voluptuous as vol
from homeassistant.components.switch import PLATFORM_SCHEMA
from homeassistant.const import DEVICE_DEFAULT_NAME
from homeassistant.helpers.entity import ToggleEntity

_LOGGER = logging.getLogger(__name__)

CONF_PULL_MODE = 'pull_mode'
CONF_PORTS = 'ports'
CONF_INVERT_LOGIC = 'invert_logic'

DEFAULT_INVERT_LOGIC = False

_SWITCHES_SCHEMA = vol.Schema({
    cv.positive_int: cv.string,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PORTS): _SWITCHES_SCHEMA,
    vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
})


# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the mraa GPIO devices."""
    invert_logic = config.get(CONF_INVERT_LOGIC)

    switches = []
    ports = config.get(CONF_PORTS)
    for port, name in ports.items():
        switches.append(MRAAGPIOSwitch(name, port, invert_logic))
    add_devices(switches)


class MRAAGPIOSwitch(ToggleEntity):
    """Representation of a  Mraa GPIO."""

    def __init__(self, name, port, invert_logic):
        """Initialize the pin."""
        self._name = name or DEVICE_DEFAULT_NAME
        self._port = port
        self._invert_logic = invert_logic
        self._state = False
        self._gpio = mraa.Gpio(self._port)
        self._gpio.dir(mraa.DIR_OUT)
        self._gpio.write(1 if self._invert_logic else 0)

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    def turn_on(self):
        """Turn the device on."""
        self._gpio.write(0 if self._invert_logic else 1)
        self._state = True
        self.update_ha_state()

    def turn_off(self):
        """Turn the device off."""
        self._gpio.write(1 if self._invert_logic else 0)
        self._state = False
        self.update_ha_state()
