import unittest
from unittest.mock import Mock

from w1thermsensor import W1ThermSensor
import w1thermsensor.errors as w1errors

from app.hardware.therm_sensor_api import ThermSensorApi
from app.hardware.therm_sensor_api import NoSensorFoundError, SensorNotReadyError, ThermSensorError


class ThermSensorApiTestCase(unittest.TestCase):
    MOCKED_SENSORS = [
        {'id': '100001', 'temp': 35.1},
        {'id': '100002', 'temp': 36.2},
        {'id': '100003', 'temp': 37.9},
    ]

    def setUp(self):
        self.mocked_sensors = []
        for mock_data in self.MOCKED_SENSORS:
            sensor = Mock(spec=W1ThermSensor)
            sensor.id = mock_data['id']
            sensor.get_temperature = Mock(return_value=mock_data['temp'])
            self.mocked_sensors.append(sensor)
        W1ThermSensor.get_available_sensors = Mock(return_value=self.mocked_sensors)

    def test_should_return_proper_id_list(self):
        api = ThermSensorApi()
        detected_sensors = api.get_sensor_id_list()

        W1ThermSensor.get_available_sensors.assert_called_once_with()
        self.assertEqual(len(detected_sensors), len(self.MOCKED_SENSORS))
        for index in range(len(self.MOCKED_SENSORS)):
            self.assertEqual(detected_sensors[index], self.MOCKED_SENSORS[index]['id'])

    def test_should_return_temperature_for_sensor(self):
        api = ThermSensorApi()

        for index in range(len(self.MOCKED_SENSORS)):
            temp = api.get_sensor_temperature(self.MOCKED_SENSORS[index]['id'])
            self.assertEqual(temp, self.MOCKED_SENSORS[index]['temp'])

    def test_should_raise_error_on_reading_temperature_when_sensor_not_found(self):
        api = ThermSensorApi()
        with self.assertRaises(NoSensorFoundError):
            api.get_sensor_temperature("invalid_id")

    def test_should_raise_error_on_reading_temperature_when_lib_raised_error(self):
        api = ThermSensorApi()
        self.mocked_sensors[0].get_temperature = Mock(side_effect=w1errors.NoSensorFoundError("name", "id"))
        self.mocked_sensors[1].get_temperature = Mock(side_effect=w1errors.SensorNotReadyError(self.mocked_sensors[1]))
        self.mocked_sensors[2].get_temperature = Mock(side_effect=w1errors.ResetValueError(self.mocked_sensors[1]))

        with self.assertRaises(NoSensorFoundError):
            api.get_sensor_temperature(self.MOCKED_SENSORS[0]["id"])

        with self.assertRaises(SensorNotReadyError):
            api.get_sensor_temperature(self.MOCKED_SENSORS[1]["id"])

        with self.assertRaises(SensorNotReadyError):
            api.get_sensor_temperature(self.MOCKED_SENSORS[2]["id"])

        self.mocked_sensors[0].get_temperature = Mock(side_effect=w1errors.KernelModuleLoadError())
        with self.assertRaises(ThermSensorError):
            api.get_sensor_temperature(self.MOCKED_SENSORS[0]["id"])


if __name__ == '__main__':
    unittest.main()
