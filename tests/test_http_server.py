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
        response_json = json.loads(response)
        self.assertEqual(len(response_json), 3)
        self.assertEqual(response_json[0]["id"], "1001")
        self.assertEqual(response_json[0]["name"], "sensor_1")
        self.assertEqual(response_json[1]["id"], "1002")
        self.assertEqual(response_json[1]["name"], "sensor_2")
        self.assertEqual(response_json[2]["id"], "1003")
        self.assertEqual(response_json[2]["name"], "")
