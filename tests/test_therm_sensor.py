import unittest
from app.therm_sensor import ThermSensor


class ThermSensorTestCase(unittest.TestCase):
    SENSOR_ID = "testId"

    def setUp(self):
        self.sensor = ThermSensor(self.SENSOR_ID)

    def test_should_have_correct_id_once_created(self):
        self.assertEqual(self.sensor.id, self.SENSOR_ID)

    def test_id_cannot_be_changed(self):
        with self.assertRaises(AttributeError):
            self.sensor.id = "someOtherId"

    def test_should_return_name_that_was_set(self):
        self.assertEqual(self.sensor.name, "")
        self.sensor.name = "test_name"
        self.assertEqual(self.sensor.name, "test_name")


if __name__ == '__main__':
    unittest.main()
