
class ThermSensor(object):
    """Single temperature sensor"""
    def __init__(self, sensor_id):
        super(ThermSensor, self).__init__()
        self.sensor_id = sensor_id
        self.name = ""

    def get_id(self):
        return self.sensor_id

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

