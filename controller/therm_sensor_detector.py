from w1thermsensor import W1ThermSensor
from controller.therm_sensor import ThermSensor


class ThermSensorDetector:

    def __init__(self):
        pass

    def get_sensors(self):
        w1_therm_sensors = W1ThermSensor.get_available_sensors()
        return tuple([ThermSensor(x.id) for x in w1_therm_sensors])
