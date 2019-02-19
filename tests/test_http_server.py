import json
import unittest
from unittest.mock import Mock

from app.controller import Controller
import app.http_server as server
from hardware.therm_sensor_api import SensorNotReadyError, NoSensorFoundError

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

    MOCKED_NOT_READY_SENSOR_ID = "not_ready_sensor"

    def get_mocked_therm_sensor_temperature(self, sensor_id):
        if sensor_id == self.MOCKED_NOT_READY_SENSOR_ID:
            raise SensorNotReadyError(sensor_id)
        if sensor_id in self.MOCKED_SENSORS_TEMPERATURE:
            return self.MOCKED_SENSORS_TEMPERATURE[sensor_id]
        else:
            raise NoSensorFoundError(sensor_id)

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
        self.assertEqual(response_json[0]["id"], self.MOCKED_SENSORS[0]["id"])
        self.assertEqual(response_json[0]["name"], self.MOCKED_SENSORS[0]["name"])
        self.assertEqual(response_json[1]["id"], self.MOCKED_SENSORS[1]["id"])
        self.assertEqual(response_json[1]["name"], self.MOCKED_SENSORS[1]["name"])
        self.assertEqual(response_json[2]["id"], self.MOCKED_SENSORS[2]["id"])
        self.assertEqual(response_json[2]["name"], self.MOCKED_SENSORS[2]["name"])

    def test_should_return_therm_sensor_temperature(self):
        sensor_id = self.MOCKED_SENSORS[0]["id"]
        response = self.app.get(URL_PATH + URL_RESOURCE_SENSORS + "/" + sensor_id, follow_redirects=True)
        response_json = json.loads(response.data.decode("utf-8"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_json["id"], sensor_id)
        self.assertEqual(response_json["temperature"], self.MOCKED_SENSORS_TEMPERATURE[sensor_id])

        sensor_id = self.MOCKED_SENSORS[1]["id"]
        response = self.app.get(URL_PATH + URL_RESOURCE_SENSORS + "/" + sensor_id, follow_redirects=True)
        response_json = json.loads(response.data.decode("utf-8"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_json["id"], sensor_id)
        self.assertEqual(response_json["temperature"], self.MOCKED_SENSORS_TEMPERATURE[sensor_id])

    def test_should_return_status_404_when_sensor_not_found(self):
        sensor_id = "invalid_sensor_id"
        response = self.app.get(URL_PATH + URL_RESOURCE_SENSORS + "/" + sensor_id, follow_redirects=True)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, b"")

    def test_should_return_status_403_when_sensor_not_ready(self):
        sensor_id = self.MOCKED_NOT_READY_SENSOR_ID
        response = self.app.get(URL_PATH + URL_RESOURCE_SENSORS + "/" + sensor_id, follow_redirects=True)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data, b"")
