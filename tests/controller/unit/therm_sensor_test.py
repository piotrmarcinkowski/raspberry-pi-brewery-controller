import unittest
import json

from controller.therm_sensor import ThermSensor


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

    def test_should_return_proper_json_representation(self):
        self.sensor.name = "test_name"
        serialized_to_json = self.sensor.to_json()
        deserialized_from_json = json.loads(serialized_to_json)

        self.assertEqual(len(deserialized_from_json), 2)
        self.assertEqual(deserialized_from_json['id'], self.sensor.id)
        self.assertEqual(deserialized_from_json['name'], self.sensor.name)

    def test_should_construct_sensor_from_json(self):
        sensor_json = """
            {"id": "123",
             "name": "sensor_name"}
        """
        sensor = ThermSensor.from_json(sensor_json)

        self.assertEqual(sensor.id, "123")
        self.assertEqual(sensor.name, "sensor_name")


if __name__ == '__main__':
    unittest.main()
