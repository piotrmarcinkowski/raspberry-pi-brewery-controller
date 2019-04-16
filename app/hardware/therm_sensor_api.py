import app.hardware.hw_config as hw_config
if hw_config.RUN_ON_RASPBERRY:
    from w1thermsensor import W1ThermSensor
    import w1thermsensor.errors as w1errors


class ThermSensorApi(object):
    FAKE_SENSOR_ID = "fake_sensor"
    FAKE_SENSOR_INIT_TEMP = 20
    FAKE_SENSOR_MAX_TEMP = 22
    FAKE_SENSOR_DELTA = 0.1

    def __init__(self):
        if not hw_config.RUN_ON_RASPBERRY:
            self.__fake_sensor_temperature = ThermSensorApi.FAKE_SENSOR_INIT_TEMP
            self.__fake_sensor_temperature_delta = ThermSensorApi.FAKE_SENSOR_DELTA

    def get_sensor_id_list(self) -> list:
        """
            Return IDs of all available sensors.

            :returns: a list of sensor IDs.
            :rtype: list
        """

        if hw_config.RUN_ON_RASPBERRY:
            w1_therm_sensors = W1ThermSensor.get_available_sensors()
            return tuple([x.id for x in w1_therm_sensors])
        else:
            return [ThermSensorApi.FAKE_SENSOR_ID]

    def get_sensor_temperature(self, sensor_id):
        """
            Returns the temperature in celsius
            :returns: the temperature in celsius
            :rtype: float
            :raises NoSensorFoundError: if the sensor with the given id could not be found
            :raises SensorNotReadyError: if the sensor is not ready yet
        """

        if hw_config.RUN_ON_RASPBERRY:
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
        else:
            return self.__get_fake_sensor_temperature()

    def __get_fake_sensor_temperature(self):
        self.__fake_sensor_temperature += self.__fake_sensor_temperature_delta
        if self.__fake_sensor_temperature >= ThermSensorApi.FAKE_SENSOR_MAX_TEMP:
            self.__fake_sensor_temperature_delta = -self.__fake_sensor_temperature_delta
        if self.__fake_sensor_temperature <= ThermSensorApi.FAKE_SENSOR_INIT_TEMP:
            self.__fake_sensor_temperature_delta = -self.__fake_sensor_temperature_delta

        return self.__fake_sensor_temperature


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
