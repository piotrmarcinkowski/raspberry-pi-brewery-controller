import unittest

from controller.therm_sensor import ThermSensor


class ThermSensorTestCase(unittest.TestCase):
    SENSOR_ID = "testId"

    def setUp(self):
        self.sensor = ThermSensor(self.SENSOR_ID)

    def test_should_have_correct_id_once_created(self):
        sensor = ThermSensor(self.SENSOR_ID)
        self.assertEqual(sensor.id, self.SENSOR_ID)

    def test_id_cannot_be_changed(self):
        sensor = ThermSensor(self.SENSOR_ID)
        with self.assertRaises(AttributeError):
            sensor.id = "someOtherId"

    def test_should_return_name_that_was_set(self):
        sensor = ThermSensor(self.SENSOR_ID)
        self.assertEqual(sensor.name, "")
        sensor.name = "test_name"
        self.assertEqual(sensor.name, "test_name")


if __name__ == '__main__':
    unittest.main()
