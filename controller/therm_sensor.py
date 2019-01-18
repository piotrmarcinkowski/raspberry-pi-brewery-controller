
class ThermSensor(object):
    """Single temperature sensor"""
    def __init__(self, sensor_id):
        super(ThermSensor, self).__init__()
        self.__sensor_id = sensor_id
        self.__name = ""

    @property
    def id(self):
        return self.__sensor_id

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name):
        self.__name = name
