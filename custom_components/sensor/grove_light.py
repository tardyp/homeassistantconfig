import mraa
from homeassistant.helpers.entity import Entity


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""
    port = config.get("port")
    add_devices([GroveLight(port)])


class GroveLight(Entity):
    """Representation of a Sensor."""
    def __init__(self, port):
        self._aio = mraa.Aio(port)
        self._state = None

    @property
    def unit_of_measurement(self):
        return "lux"

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Luminosity"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self):
        """Get the latest data from the aio and updates the states."""

        # rough conversion to lux, using formula from Grove Starter Kit booklet
        a = self._aio.read()
        if a == -1.0 or a == 0:
            self._state = -1
            return
        self._state = 10000.0 / pow(((1023.0 - a) * 10.0 / a) * 15.0, 4.0 / 3.0)
