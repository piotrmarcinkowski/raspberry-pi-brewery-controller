from w1thermsensor import W1ThermSensor


class ThermSensorApi(object):

    def get_sensor_id_list(self):
        w1_therm_sensors = W1ThermSensor.get_available_sensors()
        return tuple([x.id for x in w1_therm_sensors])

    def get_sensor_temperature(self, sensor_id):
        return 0.0