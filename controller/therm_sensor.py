
class ThermSensor(object):
	"""Single themperature sensor"""
	def __init__(self):
		super(ThermSensor, self).__init__()
                self.name = ""
	
	def set_name(self, name):
		self.name = name

	def get_name(self):
		return self.name	

