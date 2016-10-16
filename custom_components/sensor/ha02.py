import time

import mraa
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import Entity

TH02_ADDR                = 0x40
TH02_REG_STATUS          = 0x00
TH02_REG_DATA_H          = 0x01
TH02_REG_DATA_L          = 0x02
TH02_REG_CONFIG          = 0x03
TH02_REG_ID              = 0x11

TH02_STATUS_RDY_MASK     = 0x01

TH02_CMD_MEASURE_HUMI    = 0x01
TH02_CMD_MEASURE_TEMP    = 0x11

SENSOR_TEMPERATURE = "temperature"
SENSOR_HUMIDITY = "humidity"


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""
    port = config.get("i2c_port")
    add_devices([Th02Sensor(port, SENSOR_TEMPERATURE), Th02Sensor(port, SENSOR_HUMIDITY)])


class Th02Sensor(Entity):
    """Representation of a Sensor."""
    def __init__(self, i2c_port, type):
        self._sensor = mraa.I2c(i2c_port)
        self._sensor.address(TH02_ADDR)
        assert self._sensor.readReg(TH02_REG_ID) == 0x50
        self.type = type
        self._state = None
        if self.type == SENSOR_HUMIDITY:
            self._unit_of_measurement = "%"
        elif self.type == SENSOR_TEMPERATURE:
            self._unit_of_measurement = TEMP_CELSIUS

    @property
    def unit_of_measurement(self):
        return self._unit_of_measurement

    @property
    def name(self):
        """Return the name of the sensor."""
        return self.type

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def get_temp(self):
        self._sensor.writeReg(TH02_REG_CONFIG, TH02_CMD_MEASURE_TEMP)
        self.waitStatus()
        temperature = self._sensor.readReg(TH02_REG_DATA_H) << 8
        temperature |= self._sensor.readReg(TH02_REG_DATA_L)
        temperature = temperature >> 2
        temperature = (temperature / 32) - 50
        if temperature < 0 and temperature > 40:
            # probably bad read
            return None
        return temperature

    def get_humidity(self):
        self._sensor.writeReg(TH02_REG_CONFIG, TH02_CMD_MEASURE_HUMI)
        self.waitStatus()
        humidity = self._sensor.readReg(TH02_REG_DATA_H) << 8
        humidity |= self._sensor.readReg(TH02_REG_DATA_L)
        humidity = humidity >> 4
        humidity = (humidity / 16.0) - 24.0
        return humidity

    def waitStatus(self):
        for i in range(100):
            if (self._sensor.readReg(TH02_REG_STATUS) & TH02_STATUS_RDY_MASK) == 0:
                return
            time.sleep(0.01)

    def update(self):
        """Get the latest data from the TH02 and updates the states."""
        try:
            if self.type == SENSOR_HUMIDITY:
                self._state = self.get_humidity()

            if self.type == SENSOR_TEMPERATURE:
                self._state = self.get_temp()
        except Exception:
            self._state = None
