import unittest
from unittest.mock import Mock

from app.controller import Controller
from app.hardware.therm_sensor_api import ThermSensorApi


class ControllerTestCase(unittest.TestCase):
    MOCKED_SENSOR_IDS = ["1001", "1002"]
    MOCKED_SENSOR_TEMP = {"1001": 12.3, "1002": 23.4}

    def mock_get_sensor_temp(self, sensor_id):
        return self.MOCKED_SENSOR_TEMP[sensor_id]

    def test_should_return_therm_sensor_list(self):
        therm_sensor_api_mock = Mock(spec=ThermSensorApi)
        therm_sensor_api_mock.get_sensor_id_list = Mock(return_value=self.MOCKED_SENSOR_IDS)
        controller = Controller(therm_sensor_api=therm_sensor_api_mock)
        sensors = controller.get_therm_sensors()
        self.assertEqual(len(sensors), len(self.MOCKED_SENSOR_IDS))
        for index in range(len(self.MOCKED_SENSOR_IDS)):
            self.assertEqual(sensors[index].id, self.MOCKED_SENSOR_IDS[index])

    def test_should_return_therm_sensor_temperature(self):
        therm_sensor_api_mock = Mock(spec=ThermSensorApi)
        therm_sensor_api_mock.get_sensor_temperature = Mock(side_effect=self.mock_get_sensor_temp)
        controller = Controller(therm_sensor_api=therm_sensor_api_mock)

        for sensor_id in self.MOCKED_SENSOR_IDS:
            temperature = controller.get_therm_sensor_temperature(sensor_id)
            self.assertEqual(temperature, self.MOCKED_SENSOR_TEMP[sensor_id])
