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

    def to_json_data(self):
        return {"id": self.id, "name": self.name}

    @classmethod
    def from_json_data(cls, json_data):
        return ThermSensor(json_data["id"], json_data["name"])

    def __eq__(self, other):
        if type(other) is type(self):
            return self.id == other.id and \
                   self.name == other.name

        return False

    def __str__(self):
        return "Sensor [sensor_id:{} sensor_name:{}]".format(self.id, self.name)
