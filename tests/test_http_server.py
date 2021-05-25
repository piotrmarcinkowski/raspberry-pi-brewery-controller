import json
import unittest
from datetime import datetime

import app.http_server as server
from app.program import Program
from app.logger import Logger, LogEntry
from mocks import ControllerMock, ThermSensorApiMock

URL_PATH = "/brewery/api/v1.0/"
URL_RESOURCE_SENSORS = "therm_sensors"
URL_RESOURCE_PROGRAMS = "programs"
URL_RESOURCE_STATES = "states"
URL_RESOURCE_LOGS = "logs"


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
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.data.decode("utf-8"))
        self.assertEqual(len(ThermSensorApiMock.MOCKED_SENSORS), len(response_json), 4)
        self.assertEqual(response_json[0]["id"], ThermSensorApiMock.MOCKED_SENSORS[0])
        self.assertEqual(response_json[1]["id"], ThermSensorApiMock.MOCKED_SENSORS[1])
        self.assertEqual(response_json[2]["id"], ThermSensorApiMock.MOCKED_SENSORS[2])
        self.assertEqual(response_json[3]["id"], ThermSensorApiMock.MOCKED_SENSORS[3])

    def test_should_return_therm_sensor_temperature(self):
        sensor_id = ThermSensorApiMock.MOCKED_SENSORS[0]
        response = self.app.get(URL_PATH + URL_RESOURCE_SENSORS + "/" + sensor_id, follow_redirects=True)
        response_json = json.loads(response.data.decode("utf-8"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_json["id"], sensor_id)
        self.assertEqual(response_json["temperature"], ThermSensorApiMock.MOCKED_SENSORS_TEMPERATURE[sensor_id])

        sensor_id = ThermSensorApiMock.MOCKED_SENSORS[1]
        response = self.app.get(URL_PATH + URL_RESOURCE_SENSORS + "/" + sensor_id, follow_redirects=True)
        response_json = json.loads(response.data.decode("utf-8"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_json["id"], sensor_id)
        self.assertEqual(response_json["temperature"], ThermSensorApiMock.MOCKED_SENSORS_TEMPERATURE[sensor_id])

    def test_should_return_status_404_when_sensor_not_found(self):
        sensor_id = "invalid_sensor_id"
        response = self.app.get(URL_PATH + URL_RESOURCE_SENSORS + "/" + sensor_id, follow_redirects=True)
        self.assertEqual(response.status_code, 404)
        self.assertNotEqual(response.data, b"")

    def test_should_return_status_403_when_sensor_not_ready(self):
        sensor_id = ThermSensorApiMock.MOCKED_NOT_READY_SENSOR_ID
        response = self.app.get(URL_PATH + URL_RESOURCE_SENSORS + "/" + sensor_id, follow_redirects=True)
        self.assertEqual(response.status_code, 403)
        self.assertNotEqual(response.data, b"")

    def test_should_create_program(self):
        request_content = {"name": "test_program_name", "sensor_id": ThermSensorApiMock.MOCKED_SENSORS[0],
                           "heating_relay_index": 1, "cooling_relay_index": 2,
                           "min_temp": 16.0, "max_temp": 18.0, "active": True}
        expected_generated_id = self.controller_mock.get_next_program_id()
        response = self.app.post(URL_PATH + URL_RESOURCE_PROGRAMS, follow_redirects=True,
                                 json=request_content)
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.data.decode("utf-8"))
        created_program = Program.from_json_data(response_json)
        self.assertEqual(expected_generated_id, created_program.program_id)
        self.assertEqual(request_content["name"], created_program.program_name)
        self.assertTrue(len(created_program.program_crc) > 0, "Crc should not be empty")
        self.assertEqual(request_content["sensor_id"], created_program.sensor_id)
        self.assertEqual(request_content["cooling_relay_index"], created_program.cooling_relay_index)
        self.assertEqual(request_content["heating_relay_index"], created_program.heating_relay_index)
        self.assertEqual(request_content["min_temp"], created_program.min_temperature)
        self.assertEqual(request_content["max_temp"], created_program.max_temperature)
        self.assertEqual(request_content["active"], created_program.active)

    def test_should_modify_program(self):
        request_content = {"sensor_id": ThermSensorApiMock.MOCKED_SENSORS[0], "heating_relay_index": 1,
                           "cooling_relay_index": 2, "min_temp": 16.0, "max_temp": 18.0, "active": True}
        response = self.app.post(URL_PATH + URL_RESOURCE_PROGRAMS, follow_redirects=True,
                                 json=request_content)
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.data.decode("utf-8"))
        created_program = Program.from_json_data(response_json)

        request_content = {"sensor_id": ThermSensorApiMock.MOCKED_SENSORS[1], "heating_relay_index": 3,
                           "cooling_relay_index": 4, "min_temp": 17.0, "max_temp": 19.0, "active": False}
        response = self.app.put(URL_PATH + URL_RESOURCE_PROGRAMS + "/" + created_program.program_id, follow_redirects=True,
                                 json=request_content)
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.data.decode("utf-8"))
        modified_program = Program.from_json_data(response_json)
        self.assertEqual(created_program.program_id, modified_program.program_id)
        self.assertTrue(len(modified_program.program_crc) > 0, "Crc should not be empty")
        self.assertNotEqual(created_program.program_crc, modified_program.program_crc)
        self.assertEqual(modified_program.sensor_id, request_content["sensor_id"])
        self.assertEqual(modified_program.cooling_relay_index, request_content["cooling_relay_index"])
        self.assertEqual(modified_program.heating_relay_index, request_content["heating_relay_index"])
        self.assertEqual(modified_program.min_temperature, request_content["min_temp"])
        self.assertEqual(modified_program.max_temperature, request_content["max_temp"])
        self.assertEqual(modified_program.active, request_content["active"])

    def test_should_delete_program(self):
        request_content = {"sensor_id": ThermSensorApiMock.MOCKED_SENSORS[0], "heating_relay_index": 1,
                           "cooling_relay_index": 2, "min_temp": 16.0, "max_temp": 18.0, "active": True}
        response = self.app.post(URL_PATH + URL_RESOURCE_PROGRAMS, follow_redirects=True,
                                 json=request_content)
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.data.decode("utf-8"))
        created_program = Program.from_json_data(response_json)

        response = self.app.delete(URL_PATH + URL_RESOURCE_PROGRAMS + "/" + created_program.program_id, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"")
        self.assertEqual(len(self.controller_mock.programs), 0)

    def test_should_return_status_403_when_program_creation_was_rejected(self):
        request_content = {"sensor_id": ThermSensorApiMock.MOCKED_SENSORS[0], "heating_relay_index": 1,
                           "cooling_relay_index": 2, "min_temp": 16.0, "max_temp": 18.0, "active": True}
        self.controller_mock.raise_error_on_program_create()
        response = self.app.post(URL_PATH + URL_RESOURCE_PROGRAMS, follow_redirects=True,
                                 json=request_content)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data, ControllerMock.DEFAULT_ERROR_MESSAGE.encode("utf-8"))

    def test_should_return_status_403_when_program_modification_was_rejected(self):
        request_content = {"sensor_id": ThermSensorApiMock.MOCKED_SENSORS[0], "heating_relay_index": 1,
                           "cooling_relay_index": 2, "min_temp": 16.0, "max_temp": 18.0, "active": True}
        self.controller_mock.raise_error_on_program_modify()
        response = self.app.put(URL_PATH + URL_RESOURCE_PROGRAMS + "/0", follow_redirects=True,
                                 json=request_content)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data, ControllerMock.DEFAULT_ERROR_MESSAGE.encode("utf-8"))

    def test_should_return_status_404_on_modify_when_invalid_program_id(self):
        request_content = {"sensor_id": ThermSensorApiMock.MOCKED_SENSORS[0], "heating_relay_index": 1,
                           "cooling_relay_index": 2, "min_temp": 16.0, "max_temp": 18.0, "active": True}
        response = self.app.put(URL_PATH + URL_RESOURCE_PROGRAMS + "/invalid_program_id", follow_redirects=True,
                                 json=request_content)
        self.assertEqual(response.status_code, 404)

    def test_should_return_status_403_when_program_deletion_was_rejected(self):
        self.controller_mock.raise_error_on_program_delete()
        response = self.app.delete(URL_PATH + URL_RESOURCE_PROGRAMS + "/0", follow_redirects=True)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data, ControllerMock.DEFAULT_ERROR_MESSAGE.encode("utf-8"))

    def test_should_return_status_404_on_delete_when_invalid_program_id(self):
        response = self.app.delete(URL_PATH + URL_RESOURCE_PROGRAMS + "/invalid_program_id", follow_redirects=True)
        self.assertEqual(response.status_code, 404)

    def test_should_return_existing_programs(self):
        self.controller_mock.programs.append(Program("program_id1", "program_name1", "sensor_id1", 2, 4, 15.0, 15.5, active=True))
        self.controller_mock.programs.append(Program("program_id2", "program_name2", "sensor_id2", 1, 5, 15.1, 15.8, active=False))

        response = self.app.get(URL_PATH + URL_RESOURCE_PROGRAMS, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.data.decode("utf-8"))
        self.assertEqual(response_json[0]["id"], "program_id1")
        self.assertEqual(response_json[0]["name"], "program_name1")
        self.assertEqual(response_json[0]["sensor_id"], "sensor_id1")
        self.assertEqual(response_json[0]["heating_relay_index"], 2)
        self.assertEqual(response_json[0]["cooling_relay_index"], 4)
        self.assertEqual(response_json[0]["min_temp"], 15.0)
        self.assertEqual(response_json[0]["max_temp"], 15.5)
        self.assertEqual(response_json[0]["active"], True)
        self.assertEqual(response_json[1]["id"], "program_id2")
        self.assertEqual(response_json[1]["name"], "program_name2")
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

    def test_should_return_current_temperature_of_the_given_program(self):
        sensor = ThermSensorApiMock.MOCKED_SENSORS[0]
        created_program = self.__create_program(sensor, 2, 4, 15.0, 15.5, True)

        response = self.app.get(URL_PATH + URL_RESOURCE_STATES + "/" + created_program.program_id,
                                follow_redirects=True)
        self.assertEqual(200, response.status_code)
        response_json = json.loads(response.data.decode("utf-8"))
        self.assertEqual(ThermSensorApiMock.MOCKED_SENSORS_TEMPERATURE[sensor], response_json["current_temperature"])
        self.assertEqual(created_program.program_id, response_json["program_id"])
        self.assertEqual(created_program.program_crc, response_json["program_crc"])

    def test_should_return_states_of_all_available_programs(self):
        sensor1 = ThermSensorApiMock.MOCKED_SENSORS[0]
        created_program1 = self.__create_program(sensor1, 2, 4, 15.0, 15.5, True)
        sensor2 = ThermSensorApiMock.MOCKED_SENSORS[1]
        created_program2 = self.__create_program(sensor2, 1, 3, 16.0, 16.5, True)

        response = self.app.get(URL_PATH + URL_RESOURCE_STATES, follow_redirects=True)

        self.assertEqual(200, response.status_code)
        response_json = json.loads(response.data.decode("utf-8"))
        self.assertEqual(ThermSensorApiMock.MOCKED_SENSORS_TEMPERATURE[sensor1], response_json[0]["current_temperature"])
        self.assertEqual(created_program1.program_id, response_json[0]["program_id"])

        self.assertEqual(ThermSensorApiMock.MOCKED_SENSORS_TEMPERATURE[sensor2], response_json[1]["current_temperature"])
        self.assertEqual(created_program2.program_id, response_json[1]["program_id"])

    def test_should_return_current_relay_state_of_the_given_program(self):
        sensor = ThermSensorApiMock.MOCKED_SENSORS[0]
        cooling_relay = 2
        heating_relay = 4

        created_program = self.__create_program(sensor, heating_relay, cooling_relay, 6.0, 15.5, True)

        test_data = [
            {"temperature": 15.2, "heating_relay": 0, "cooling_relay": 0},
            {"temperature": 15.6, "heating_relay": 0, "cooling_relay": 1},
            {"temperature": 15.1, "heating_relay": 0, "cooling_relay": 0},
            {"temperature": 14.9, "heating_relay": 1, "cooling_relay": 0},
            {"temperature": 15.3, "heating_relay": 0, "cooling_relay": 0}
        ]

        for data in test_data:
            sensor_temp = data["temperature"]
            self.controller_mock.set_sensor_temperature(sensor, sensor_temp)
            self.controller_mock.set_relay_state(cooling_relay, data["cooling_relay"])
            self.controller_mock.set_relay_state(heating_relay, data["heating_relay"])
            response = self.app.get(URL_PATH + URL_RESOURCE_STATES + "/" + created_program.program_id,
                                    follow_redirects=True)
            self.assertEqual(200, response.status_code)
            response_json = json.loads(response.data.decode("utf-8"))
            self.assertEqual(sensor_temp, response_json["current_temperature"])
            self.assertEqual(data["heating_relay"], response_json["heating_activated"], "Temperature: {}".format(sensor_temp))
            self.assertEqual(data["cooling_relay"], response_json["cooling_activated"], "Temperature: {}".format(sensor_temp))

    def test_should_return_different_crc_if_given_program_has_changed(self):
        sensor = ThermSensorApiMock.MOCKED_SENSORS[0]
        cooling_relay = 2
        heating_relay = 4

        created_program = self.__create_program(sensor, heating_relay, cooling_relay, 15.0, 15.5, True)

        # get program state and store its crc
        response = self.app.get(URL_PATH + URL_RESOURCE_STATES + "/" + created_program.program_id,
                                follow_redirects=True)
        self.assertEqual(200, response.status_code)
        response_json = json.loads(response.data.decode("utf-8"))
        crc = response_json["program_crc"]

        # now modify the program
        request_content = {"sensor_id": sensor, "heating_relay_index": 3,
                           "cooling_relay_index": 4, "min_temp": 17.0, "max_temp": 19.0, "active": False}
        response = self.app.put(URL_PATH + URL_RESOURCE_PROGRAMS + "/" + created_program.program_id,
                                follow_redirects=True,
                                json=request_content)
        self.assertEqual(200, response.status_code)

        # get modified program state
        response = self.app.get(URL_PATH + URL_RESOURCE_STATES + "/" + created_program.program_id,
                                follow_redirects=True)
        response_json = json.loads(response.data.decode("utf-8"))
        new_crc = response_json["program_crc"]

        self.assertNotEqual(crc, new_crc)

    def __create_program(self, sensor, heating_relay, cooling_relay, min_temp, max_temp, active):
        request_content = {"name": "test_program_name", "sensor_id": sensor,
                           "heating_relay_index": heating_relay, "cooling_relay_index": cooling_relay,
                           "min_temp": min_temp, "max_temp": max_temp, "active": active}
        response = self.app.post(URL_PATH + URL_RESOURCE_PROGRAMS, follow_redirects=True,
                                 json=request_content)
        return self.controller_mock.programs[-1]
