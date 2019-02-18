import json
import unittest
from unittest.mock import Mock

from app.controller import Controller
import app.http_server as server

URL_PATH = "/brewery/api/v1.0/"
URL_RESOURCE_SENSORS = "therm_sensors"


class HttpServerTestCase(unittest.TestCase):
    MOCKED_SENSORS = [
        {"id": "1001", "name": "sensor_1"},
        {"id": "1002", "name": "sensor_2"},
        {"id": "1003", "name": ""}
    ]

    MOCKED_SENSORS_TEMPERATURE = {
        "1001": 20.123,
        "1002": 19.234,
        "1003": 18.345
    }

    def get_mocked_therm_sensor_temperature(self, sensor_id):
        return self.MOCKED_SENSORS_TEMPERATURE[sensor_id]

    def setUp(self):
        self.controller_mock = Mock(spec=Controller)
        self.sensor_mock_list = []
        for sensor_data in self.MOCKED_SENSORS:
            sensor_mock = Mock()
            sensor_mock.id = sensor_data["id"]
            sensor_mock.name = sensor_data["name"]
            self.sensor_mock_list.append(sensor_mock)

        # mock controller
        self.controller_mock.get_therm_sensors = Mock(return_value=self.sensor_mock_list)
        self.controller_mock.get_therm_sensor_temperature = Mock(side_effect=self.get_mocked_therm_sensor_temperature)
        server.init(self.controller_mock)

        # create a test client
        self.app = server.app.test_client()
        # propagate the exceptions to the test client
        self.app.testing = True

    def test_should_return_list_of_available_therm_sensors(self):
        response = self.app.get(URL_PATH + URL_RESOURCE_SENSORS, follow_redirects=True)
        response_json = json.loads(response.data.decode("utf-8"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response_json), 3)
        self.assertEqual(response_json[0]["id"], "1001")
        self.assertEqual(response_json[0]["name"], "sensor_1")
        self.assertEqual(response_json[1]["id"], "1002")
        self.assertEqual(response_json[1]["name"], "sensor_2")
        self.assertEqual(response_json[2]["id"], "1003")
        self.assertEqual(response_json[2]["name"], "")

    def test_should_return_therm_sensor_temperature(self):
        response = self.app.get(URL_PATH + URL_RESOURCE_SENSORS + "/1001", follow_redirects=True)
        response_json = json.loads(response.data.decode("utf-8"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_json["id"], "1001")
        self.assertEqual(response_json["temperature"], self.MOCKED_SENSORS_TEMPERATURE["1001"])

        response = self.app.get(URL_PATH + URL_RESOURCE_SENSORS + "/1002", follow_redirects=True)
        response_json = json.loads(response.data.decode("utf-8"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_json["id"], "1002")
        self.assertEqual(response_json["temperature"], self.MOCKED_SENSORS_TEMPERATURE["1002"])
