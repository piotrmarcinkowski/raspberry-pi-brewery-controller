import app.hardware.hw_config as hw_config
from app.hardware.fake_hw import FakeHardware

if hw_config.RUN_ON_RASPBERRY:
    from w1thermsensor import W1ThermSensor
    import w1thermsensor.errors as w1errors


class ThermSensorApi(object):

    def __init__(self):
        pass

    def get_sensor_id_list(self) -> list:
        """
            Return IDs of all available sensors.

            :returns: a list of sensor IDs.
            :rtype: list
        """

        w1_therm_sensors = W1ThermSensor.get_available_sensors()
        return tuple([x.id for x in w1_therm_sensors])

    def get_sensor_temperature(self, sensor_id):
        """
            Returns the temperature in celsius
            :returns: the temperature in celsius
            :rtype: float
            :raises NoSensorFoundError: if the sensor with the given id could not be found
            :raises SensorNotReadyError: if the sensor is not ready yet
        """
        w1_therm_sensors = W1ThermSensor.get_available_sensors()
        for sensor in w1_therm_sensors:
            if sensor.id == sensor_id:
                try:
                    return sensor.get_temperature()
                except w1errors.NoSensorFoundError:
                    raise NoSensorFoundError(sensor_id)
                except w1errors.ResetValueError:
                    raise SensorNotReadyError(sensor_id)
                except w1errors.SensorNotReadyError:
                    raise SensorNotReadyError(sensor_id)
                except w1errors.W1ThermSensorError:
                    raise ThermSensorError()

        raise NoSensorFoundError(sensor_id)


class ThermSensorError(Exception):
    """Exception base-class for ThermSensor errors"""

    pass


class NoSensorFoundError(ThermSensorError):
    """Exception when no sensor is found"""

    def __init__(self, sensor_id):
        super(NoSensorFoundError, self).__init__(
            "No sensor with id '{0}' found".format(sensor_id)
        )


class SensorNotReadyError(ThermSensorError):
    """Exception when the sensor is not ready yet"""

    def __init__(self, sensor_id):
        super(SensorNotReadyError, self).__init__(
            "Sensor {} is not yet ready to read temperature".format(sensor_id)
        )
