import json
import unittest
from datetime import datetime
from datetime import timedelta
from unittest.mock import Mock

from app.controller import Controller, ProgramError
import app.http_server as server
from app.hardware.therm_sensor_api import SensorNotReadyError, NoSensorFoundError
from app.program import Program
from app.logger import Logger, LogEntry

URL_PATH = "/brewery/api/v1.0/"
URL_RESOURCE_SENSORS = "therm_sensors"
URL_RESOURCE_PROGRAMS = "programs"
URL_RESOURCE_LOGS = "logs"


class ControllerMock(Mock):
    MOCKED_NOT_READY_SENSOR_ID = "not_ready_sensor"
    DEFAULT_ERROR_MESSAGE = "Error message"

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
        self.modify_program = Mock(side_effect=self.__mocked_modify_program)
        self.delete_program = Mock(side_effect=self.__mocked_delete_program)
        self.get_programs = Mock(side_effect=self.__mocked_get_programs)
        self.programs = []
        self.__temperatures = {}

    def raise_error_on_program_create(self):
        self.create_program = Mock(side_effect=ProgramError(ControllerMock.DEFAULT_ERROR_MESSAGE))

    def raise_error_on_program_modify(self):
        self.modify_program = Mock(side_effect=ProgramError(ControllerMock.DEFAULT_ERROR_MESSAGE))

    def raise_error_on_program_delete(self):
        self.delete_program = Mock(side_effect=ProgramError(ControllerMock.DEFAULT_ERROR_MESSAGE))

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

    def __mocked_modify_program(self, program_index, program):
        self.programs[program_index] = program

    def __mocked_delete_program(self, program_index):
        del self.programs[program_index]

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
        self.assertNotEqual(response.data, b"")

    def test_should_return_status_403_when_sensor_not_ready(self):
        sensor_id = ControllerMock.MOCKED_NOT_READY_SENSOR_ID
        response = self.app.get(URL_PATH + URL_RESOURCE_SENSORS + "/" + sensor_id, follow_redirects=True)
        self.assertEqual(response.status_code, 403)
        self.assertNotEqual(response.data, b"")

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

    def test_should_modify_program(self):
        request_content = {"sensor_id": ControllerMock.MOCKED_SENSORS[0]["id"], "heating_relay_index": 1,
                           "cooling_relay_index": 2, "min_temp": 16.0, "max_temp": 18.0, "active": True}
        response = self.app.post(URL_PATH + URL_RESOURCE_PROGRAMS, follow_redirects=True,
                                 json=json.dumps(request_content))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"")

        request_content = {"sensor_id": ControllerMock.MOCKED_SENSORS[1]["id"], "heating_relay_index": 3,
                           "cooling_relay_index": 4, "min_temp": 17.0, "max_temp": 19.0, "active": False}
        response = self.app.put(URL_PATH + URL_RESOURCE_PROGRAMS + "/0", follow_redirects=True,
                                 json=json.dumps(request_content))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"")

        modified_program = self.controller_mock.programs[0]
        self.assertEqual(modified_program.sensor_id, request_content["sensor_id"])
        self.assertEqual(modified_program.cooling_relay_index, request_content["cooling_relay_index"])
        self.assertEqual(modified_program.heating_relay_index, request_content["heating_relay_index"])
        self.assertEqual(modified_program.min_temperature, request_content["min_temp"])
        self.assertEqual(modified_program.max_temperature, request_content["max_temp"])
        self.assertEqual(modified_program.active, request_content["active"])

    def test_should_delete_program(self):
        request_content = {"sensor_id": ControllerMock.MOCKED_SENSORS[0]["id"], "heating_relay_index": 1,
                           "cooling_relay_index": 2, "min_temp": 16.0, "max_temp": 18.0, "active": True}
        response = self.app.post(URL_PATH + URL_RESOURCE_PROGRAMS, follow_redirects=True,
                                 json=json.dumps(request_content))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"")

        response = self.app.delete(URL_PATH + URL_RESOURCE_PROGRAMS + "/0", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"")
        self.assertEqual(len(self.controller_mock.programs), 0)

    def test_should_return_status_403_when_program_creation_was_rejected(self):
        request_content = {"sensor_id": ControllerMock.MOCKED_SENSORS[0]["id"], "heating_relay_index": 1,
                           "cooling_relay_index": 2, "min_temp": 16.0, "max_temp": 18.0, "active": True}
        self.controller_mock.raise_error_on_program_create()
        response = self.app.post(URL_PATH + URL_RESOURCE_PROGRAMS, follow_redirects=True,
                                 json=json.dumps(request_content))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data, ControllerMock.DEFAULT_ERROR_MESSAGE.encode("utf-8"))

    def test_should_return_status_403_when_program_modification_was_rejected(self):
        request_content = {"sensor_id": ControllerMock.MOCKED_SENSORS[0]["id"], "heating_relay_index": 1,
                           "cooling_relay_index": 2, "min_temp": 16.0, "max_temp": 18.0, "active": True}
        self.controller_mock.raise_error_on_program_modify()
        response = self.app.put(URL_PATH + URL_RESOURCE_PROGRAMS + "/0", follow_redirects=True,
                                 json=json.dumps(request_content))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data, ControllerMock.DEFAULT_ERROR_MESSAGE.encode("utf-8"))

    def test_should_return_status_500_on_modify_when_error_parsing_program_index(self):
        request_content = {"sensor_id": ControllerMock.MOCKED_SENSORS[0]["id"], "heating_relay_index": 1,
                           "cooling_relay_index": 2, "min_temp": 16.0, "max_temp": 18.0, "active": True}
        response = self.app.put(URL_PATH + URL_RESOURCE_PROGRAMS + "/not_int", follow_redirects=True,
                                 json=json.dumps(request_content))
        self.assertEqual(response.status_code, 500)

    def test_should_return_status_403_when_program_deletion_was_rejected(self):
        self.controller_mock.raise_error_on_program_delete()
        response = self.app.delete(URL_PATH + URL_RESOURCE_PROGRAMS + "/0", follow_redirects=True)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data, ControllerMock.DEFAULT_ERROR_MESSAGE.encode("utf-8"))

    def test_should_return_status_500_on_delete_when_error_parsing_program_index(self):
        response = self.app.delete(URL_PATH + URL_RESOURCE_PROGRAMS + "/not_int", follow_redirects=True)
        self.assertEqual(response.status_code, 500)

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

    def test_should_return_logs(self):
        now = datetime.now()
        Logger.info("info msg")
        Logger.error("error msg")

        response = self.app.get(URL_PATH + URL_RESOURCE_LOGS, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.data.decode("utf-8"))

        logs_count = len(response_json)
        self.assertGreaterEqual(logs_count, 2)
        log_entry_datetime = datetime.strptime(response_json[-2]["date"], LogEntry.DATE_FORMAT)
        delta = log_entry_datetime - now
        self.assertLessEqual(delta.total_seconds(), 2)
        self.assertEqual(response_json[-2]["level"], "info")
        self.assertEqual(response_json[-2]["msg"], "info msg")
        log_entry_datetime = datetime.strptime(response_json[-1]["date"], LogEntry.DATE_FORMAT)
        delta = log_entry_datetime - now
        self.assertLessEqual(delta.total_seconds(), 2)
        self.assertEqual(response_json[-1]["level"], "error")
        self.assertEqual(response_json[-1]["msg"], "error msg")