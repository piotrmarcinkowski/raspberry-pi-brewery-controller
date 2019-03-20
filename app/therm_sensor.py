class ThermSensor(object):
    """Single temperature sensor"""

    def __init__(self, sensor_id, name=""):
        super(ThermSensor, self).__init__()
        self.__sensor_id = sensor_id
        self.__name = name

    @property
    def id(self):
        return self.__sensor_id

    @property
    def name(self):
        return self.__name
