import unittest
from unittest.mock import Mock

from app.controller import Controller
from app.hardware.therm_sensor_api import ThermSensorApi


class ControllerTestCase(unittest.TestCase):
    MOCKED_SENSOR_IDS = ["1001", "1002"]

    def test_should_return_therm_sensor_list(self):
        therm_sensor_api_mock = Mock(spec=ThermSensorApi)
        therm_sensor_api_mock.get_sensor_id_list = Mock(return_value=self.MOCKED_SENSOR_IDS)
        controller = Controller(therm_sensor_api=therm_sensor_api_mock)
        sensors = controller.get_therm_sensors()
        self.assertEqual(len(sensors), len(self.MOCKED_SENSOR_IDS))
        for index in range(len(self.MOCKED_SENSOR_IDS)):
            self.assertEqual(sensors[index].id, self.MOCKED_SENSOR_IDS[index])
