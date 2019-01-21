import json
import unittest
from unittest.mock import Mock

from app.controller import Controller
import app.http_server as server


class HttpServerTestCase(unittest.TestCase):

    MOCKED_SENSORS = [
        {"id": "1001", "name": "sensor_1"},
        {"id": "1002", "name": "sensor_2"},
        {"id": "1003", "name": ""}
    ]

    def setUp(self):
        self.controller_mock = Mock(spec=Controller)
        self.sensor_mock_list = []
        for sensor_data in self.MOCKED_SENSORS:
            sensor_mock = Mock()
            sensor_mock.id = sensor_data["id"]
            sensor_mock.name = sensor_data["name"]
            self.sensor_mock_list.append(sensor_mock)
        self.controller_mock.get_therm_sensors = Mock(return_value=self.sensor_mock_list)
        server.init(self.controller_mock)

    def test_should_return_list_of_available_therm_sensors(self):
        response = server.get_therm_sensors()
        self.assertEqual(response, '[{"id": "1001", "name": "sensor_1"}, {"id": "1002", "name": "sensor_2"}, {"id": "1003", "name": ""}]')



