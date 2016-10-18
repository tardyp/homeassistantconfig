#!/usr/bin/env python
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.climate import (ATTR_TARGET_TEMP_HIGH,
                                              ATTR_TARGET_TEMP_LOW,
                                              PLATFORM_SCHEMA, ClimateDevice)
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS

import mraa

base_cmd = [
    0x1, 0x10, 0x30, 0x40, 0xBF, 0x1, 0xFE, 0x11, 0x12, 0x1, 0x3, 0x20,
    0x0, 0x2, 0x0, 0x3, 0x0, 0x80, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x1,
    0x0, 0x0, 0]

PULSE_FREQ = 38000

START_PULSE = 30600
START_PAUSE = 51100
START_PULSE2 = 3356
START_PAUSE2 = 1723

PULSE_LEN = 430
PAUSE_HIGH = 1247
PAUSE_LOW = 430


CONF_NAME = 'name'
DEFAULT_NAME = 'AC Thermostat'
CONF_TARGET_TEMP = 'target_temp'
CONF_AWAY = 'away'
CONF_FAN_MODE = 'fan_mode'
CONF_SWING_MODE = 'swing_mode'
CONF_AC_MODE = 'ac_mode'
CONF_AUX = 'aux'
CONF_MIN_TEMP = 'min_temp'
CONF_MAX_TEMP = 'max_temp'


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_AC_MODE): cv.string,
    vol.Optional(CONF_AWAY): cv.boolean,
    vol.Optional(CONF_AUX): cv.boolean,
    vol.Optional(CONF_FAN_MODE): cv.string,
    vol.Optional(CONF_SWING_MODE): cv.string,
    vol.Optional(CONF_MAX_TEMP): vol.Coerce(float),
    vol.Optional(CONF_MIN_TEMP): vol.Coerce(float),
    vol.Optional(CONF_TARGET_TEMP): vol.Coerce(float),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the generic thermostat."""

    add_devices([HitachiThermostat(
        config.get(CONF_NAME),
        config.get(CONF_TARGET_TEMP),
        config.get(CONF_AWAY),
        config.get(CONF_FAN_MODE),
        config.get(CONF_SWING_MODE),
        config.get(CONF_AC_MODE),
        config.get(CONF_AUX),
        config.get(CONF_MAX_TEMP),
        config.get(CONF_MIN_TEMP))])


# pylint: disable=abstract-method
class HitachiThermostat(ClimateDevice):
    """Representation of a Nest thermostat."""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, name, target_temperature,
                 away, current_fan_mode,
                 current_swing_mode,
                 current_operation, aux, target_temp_high, target_temp_low):
        """Initialize the climate device."""
        self._name = name
        self._target_temperature = target_temperature
        self._unit_of_measurement = TEMP_CELSIUS
        self._away = away
        self._current_fan_mode = current_fan_mode
        self._current_operation = current_operation
        self._aux = aux
        self._current_swing_mode = current_swing_mode
        self._fan_list = ["On Low", "On High", "Auto Low", "Auto High", "Off"]
        self._operation_list = ["heat", "cool", "dry"]
        self._swing_list = ["Auto", "1", "2", "3", "Off"]
        self._max_temp = target_temp_high
        self._min_temp = target_temp_low
        self.powerful = 0
        self.eco = 0
        self.init_mraa()
        self.run_cmd()

    def init_mraa(self):
        # mraa will make sure the Pwm is configured properly
        x = mraa.Pwm(3)
        x.period_us(10)
        x.pulsewidth_us(5)
        x.enable(True)
        x.enable(False)

    def make_header(self):
        ret = ""
        for i in [PULSE_FREQ, START_PULSE, START_PAUSE, START_PULSE2,
                  START_PAUSE2, PULSE_LEN, PAUSE_HIGH, PAUSE_LOW]:
            ret += "%04X" % i
        return ret

    def create_cmd(self):
        buf = base_cmd[:]
        c = 0xc2
        buf[11] = int(self._target_temperature) << 1
        ventilation = self._fan_list.index(self._current_fan_mode)
        buf[13] = ventilation + 1
        mode = self._operation_list.index(self._current_operation) + 3
        buf[10] = mode
        if (self.powerful):
            buf[25] = 0x20
        if (self.eco):
            buf[25] = 0x02
        if (self._away):
            buf[19] = 0x0

        for i in range(27):
            c = (c + buf[i]) & 0xff

        c = 0xff ^ (c - 1)
        buf[27] = c
        return self.make_header() + "".join(["%02X" % i for i in buf])

    def run_cmd(self):
        buf = self.create_cmd()
        # try:
        #     with open("/dev/ttymcu0", "w") as f:
        #         f.write("IRCODE" + buf + "\n")
        # except Exception as e:
        #     print("cannot write cmd", e)

    @property
    def should_poll(self):
        """Polling not needed for a demo climate device."""
        return False

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._target_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    @property
    def max_temp(self):
        """Return the highbound target temperature we try to reach."""
        return self._max_temp

    @property
    def min_temp(self):
        """Return the lowbound target temperature we try to reach."""
        return self._min_temp

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        return self._current_operation

    @property
    def operation_list(self):
        """List of available operation modes."""
        return self._operation_list

    @property
    def is_away_mode_on(self):
        """Return if away mode is on."""
        return self._away

    @property
    def is_aux_heat_on(self):
        """Return true if away mode is on."""
        return self._aux

    @property
    def current_fan_mode(self):
        """Return the fan setting."""
        return self._current_fan_mode

    @property
    def fan_list(self):
        """List of available fan modes."""
        return self._fan_list

    def set_temperature(self, **kwargs):
        """Set new target temperatures."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            self._target_temperature = kwargs.get(ATTR_TEMPERATURE)
            self.run_cmd()
        self.update_ha_state()

    def set_humidity(self, humidity):
        """Set new target temperature."""
        self._target_humidity = humidity
        self.run_cmd()
        self.update_ha_state()

    def set_swing_mode(self, swing_mode):
        """Set new target temperature."""
        self._current_swing_mode = swing_mode
        self.run_cmd()
        self.update_ha_state()

    def set_fan_mode(self, fan):
        """Set new target temperature."""
        self._current_fan_mode = fan
        self.run_cmd()
        self.update_ha_state()

    def set_operation_mode(self, operation_mode):
        """Set new target temperature."""
        self._current_operation = operation_mode
        self.run_cmd()
        self.update_ha_state()

    @property
    def current_swing_mode(self):
        """Return the swing setting."""
        return self._current_swing_mode

    @property
    def swing_list(self):
        """List of available swing modes."""
        return self._swing_list

    def turn_away_mode_on(self):
        """Turn away mode on."""
        self._away = True
        self.run_cmd()
        self.update_ha_state()

    def turn_away_mode_off(self):
        """Turn away mode off."""
        self._away = False
        self.run_cmd()
        self.update_ha_state()

    def turn_aux_heat_on(self):
        """Turn away auxillary heater on."""
        self._aux = True
        self.run_cmd()
        self.update_ha_state()

    def turn_aux_heat_off(self):
        """Turn auxillary heater off."""
        self._aux = False
        self.run_cmd()
        self.update_ha_state()
