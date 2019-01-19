import json

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

    def to_json(self):
        return json.dumps({'id': self.id, 'name': self.name})

    @classmethod
    def from_json(cls, sensor_json):
        data = json.loads(sensor_json)
        sensor = ThermSensor(data['id'])
        sensor.name = data['name']
        return sensor
