
class ThermSensor(object):
    """Single temperature sensor"""
    def __init__(self, id):
        super(ThermSensor, self).__init__()
        self.id = id
        self.name = ""

    def get_id(self):
        return self.id

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

