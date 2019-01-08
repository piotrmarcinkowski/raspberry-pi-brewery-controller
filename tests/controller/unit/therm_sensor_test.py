import unittest

from controller.therm_sensor import ThermSensor

class TestThermSensor(unittest.TestCase):

	def test_should_return_name_that_was_set(self):
		sensor = ThermSensor()
		sensor.set_name("test_name")
		self.assertEqual(sensor.get_name(), "test_name")

if __name__ == '__main__':
    unittest.main()
