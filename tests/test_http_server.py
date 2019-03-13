import json
import unittest
from unittest.mock import Mock

from app.controller import Controller, ProgramError
import app.http_server as server
from hardware.therm_sensor_api import SensorNotReadyError, NoSensorFoundError
from program import Program

URL_PATH = "/brewery/api/v1.0/"
URL_RESOURCE_SENSORS = "therm_sensors"
URL_RESOURCE_PROGRAMS = "programs"


class ControllerMock(Mock):
    MOCKED_NOT_READY_SENSOR_ID = "not_ready_sensor"

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

    def __init__(self):
        super().__init__(spec=Controller)
        self.__prepare_sensor_list()
        self.get_therm_sensors = Mock(return_value=self.sensor_mock_list)
        self.get_therm_sensor_temperature = Mock(side_effect=self.__mocked_get_sensor_temperature)
        self.create_program = Mock(side_effect=self.__mocked_create_program)
        self.get_programs = Mock(side_effect=self.__mocked_get_programs)
        self.programs = []
        self.__temperatures = {}

    def raise_error_on_program_create(self):
        self.create_program = Mock(side_effect=ProgramError())

    def __prepare_sensor_list(self):
        self.sensor_mock_list = []
        for sensor_data in self.MOCKED_SENSORS:
            sensor_mock = Mock()
            sensor_mock.id = sensor_data["id"]
            sensor_mock.name = sensor_data["name"]
            self.sensor_mock_list.append(sensor_mock)

    def __mocked_get_sensor_temperature(self, sensor_id):
        if sensor_id == self.MOCKED_NOT_READY_SENSOR_ID:
            raise SensorNotReadyError(sensor_id)
        if sensor_id in self.MOCKED_SENSORS_TEMPERATURE:
            return self.MOCKED_SENSORS_TEMPERATURE[sensor_id]
        else:
            raise NoSensorFoundError(sensor_id)

    def __mocked_create_program(self, program):
        self.programs.append(program)

    def __mocked_get_programs(self):
        return self.programs


class HttpServerTestCase(unittest.TestCase):

    def setUp(self):
        self.controller_mock = ControllerMock()
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
        self.assertEqual(response_json[0]["id"], ControllerMock.MOCKED_SENSORS[0]["id"])
        self.assertEqual(response_json[0]["name"], ControllerMock.MOCKED_SENSORS[0]["name"])
        self.assertEqual(response_json[1]["id"], ControllerMock.MOCKED_SENSORS[1]["id"])
        self.assertEqual(response_json[1]["name"], ControllerMock.MOCKED_SENSORS[1]["name"])
        self.assertEqual(response_json[2]["id"], ControllerMock.MOCKED_SENSORS[2]["id"])
        self.assertEqual(response_json[2]["name"], ControllerMock.MOCKED_SENSORS[2]["name"])

    def test_should_return_therm_sensor_temperature(self):
        sensor_id = ControllerMock.MOCKED_SENSORS[0]["id"]
        response = self.app.get(URL_PATH + URL_RESOURCE_SENSORS + "/" + sensor_id, follow_redirects=True)
        response_json = json.loads(response.data.decode("utf-8"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_json["id"], sensor_id)
        self.assertEqual(response_json["temperature"], ControllerMock.MOCKED_SENSORS_TEMPERATURE[sensor_id])

        sensor_id = ControllerMock.MOCKED_SENSORS[1]["id"]
        response = self.app.get(URL_PATH + URL_RESOURCE_SENSORS + "/" + sensor_id, follow_redirects=True)
        response_json = json.loads(response.data.decode("utf-8"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_json["id"], sensor_id)
        self.assertEqual(response_json["temperature"], ControllerMock.MOCKED_SENSORS_TEMPERATURE[sensor_id])

    def test_should_return_status_404_when_sensor_not_found(self):
        sensor_id = "invalid_sensor_id"
        response = self.app.get(URL_PATH + URL_RESOURCE_SENSORS + "/" + sensor_id, follow_redirects=True)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, b"")

    def test_should_return_status_403_when_sensor_not_ready(self):
        sensor_id = ControllerMock.MOCKED_NOT_READY_SENSOR_ID
        response = self.app.get(URL_PATH + URL_RESOURCE_SENSORS + "/" + sensor_id, follow_redirects=True)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data, b"")

    def test_should_create_program(self):
        request_content = {"sensor_id": ControllerMock.MOCKED_SENSORS[0]["id"], "heating_relay_index": 1,
                           "cooling_relay_index": 2, "min_temp": 16.0, "max_temp": 18.0, "active": True}
        response = self.app.post(URL_PATH + URL_RESOURCE_PROGRAMS, follow_redirects=True,
                                 json=json.dumps(request_content))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"")
        created_program = self.controller_mock.programs[0]
        self.assertEqual(created_program.sensor_id, request_content["sensor_id"])
        self.assertEqual(created_program.cooling_relay_index, request_content["cooling_relay_index"])
        self.assertEqual(created_program.heating_relay_index, request_content["heating_relay_index"])
        self.assertEqual(created_program.min_temperature, request_content["min_temp"])
        self.assertEqual(created_program.max_temperature, request_content["max_temp"])
        self.assertEqual(created_program.active, request_content["active"])

    def test_should_reject_program_with_properties_duplicated_with_existing_program(self):
        request_content = {"sensor_id": ControllerMock.MOCKED_SENSORS[0]["id"], "heating_relay_index": 1,
                           "cooling_relay_index": 2, "min_temp": 16.0, "max_temp": 18.0, "active": True}
        self.controller_mock.raise_error_on_program_create()
        response = self.app.post(URL_PATH + URL_RESOURCE_PROGRAMS, follow_redirects=True,
                                 json=json.dumps(request_content))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data, b"")

    def test_should_return_existing_programs(self):
        self.controller_mock.programs.append(Program("sensor_id1", 2, 4, 15.0, 15.5, active=True))
        self.controller_mock.programs.append(Program("sensor_id2", 1, 5, 15.1, 15.8, active=False))

        response = self.app.get(URL_PATH + URL_RESOURCE_PROGRAMS, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.data.decode("utf-8"))
        self.assertEqual(response_json[0]["sensor_id"], "sensor_id1")
        self.assertEqual(response_json[0]["heating_relay_index"], 2)
        self.assertEqual(response_json[0]["cooling_relay_index"], 4)
        self.assertEqual(response_json[0]["min_temp"], 15.0)
        self.assertEqual(response_json[0]["max_temp"], 15.5)
        self.assertEqual(response_json[0]["active"], True)
        self.assertEqual(response_json[1]["sensor_id"], "sensor_id2")
        self.assertEqual(response_json[1]["heating_relay_index"], 1)
        self.assertEqual(response_json[1]["cooling_relay_index"], 5)
        self.assertEqual(response_json[1]["min_temp"], 15.1)
        self.assertEqual(response_json[1]["max_temp"], 15.8)
        self.assertEqual(response_json[1]["active"], False)
