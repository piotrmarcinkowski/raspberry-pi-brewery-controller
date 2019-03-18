import unittest
from unittest.mock import Mock

from app.controller import Controller, ProgramError
from app.hardware.therm_sensor_api import ThermSensorApi, NoSensorFoundError, SensorNotReadyError
from app.program import Program


class ControllerTestCase(unittest.TestCase):
    MOCKED_SENSOR_IDS = ["1001", "1002"]
    MOCKED_SENSOR_TEMP = {"1001": 12.3, "1002": 23.4}

    def mock_get_sensor_temp(self, sensor_id):
        return self.MOCKED_SENSOR_TEMP[sensor_id]

    def setUp(self):
        self.therm_sensor_api_mock = Mock(spec=ThermSensorApi)
        self.therm_sensor_api_mock.get_sensor_id_list = Mock(return_value=self.MOCKED_SENSOR_IDS)
        self.therm_sensor_api_mock.get_sensor_temperature = Mock(side_effect=self.mock_get_sensor_temp)
        self.controller = Controller(therm_sensor_api=self.therm_sensor_api_mock)

    def test_should_return_therm_sensor_list(self):
        sensors = self.controller.get_therm_sensors()
        self.assertEqual(len(sensors), len(self.MOCKED_SENSOR_IDS))
        for index in range(len(self.MOCKED_SENSOR_IDS)):
            self.assertEqual(sensors[index].id, self.MOCKED_SENSOR_IDS[index])

    def test_should_return_therm_sensor_temperature(self):
        for sensor_id in self.MOCKED_SENSOR_IDS:
            temperature = self.controller.get_therm_sensor_temperature(sensor_id)
            self.assertEqual(temperature, self.MOCKED_SENSOR_TEMP[sensor_id])

    def test_should_throw_if_sensor_not_found(self):
        invalid_sensor_id = "invalid_sensor_id"
        self.therm_sensor_api_mock.get_sensor_temperature = Mock(side_effect=NoSensorFoundError(invalid_sensor_id))

        with self.assertRaises(NoSensorFoundError):
            self.controller.get_therm_sensor_temperature(invalid_sensor_id)

    def test_should_throw_if_sensor_not_ready(self):
        self.therm_sensor_api_mock.get_sensor_temperature = Mock(
            side_effect=SensorNotReadyError(self.MOCKED_SENSOR_IDS[0]))

        with self.assertRaises(SensorNotReadyError):
            self.controller.get_therm_sensor_temperature(self.MOCKED_SENSOR_IDS[0])

    def test_should_create_programs_with_given_parameters(self):
        program1 = Program("1001", 2, 4, 16.5, 17.1)
        self.controller.create_program(program1)
        program2 = Program("1002", 1, 5, 16.1, 17.4)
        self.controller.create_program(program2)
        programs = self.controller.get_programs()
        self.assertEqual(programs[0], program1)
        self.assertEqual(programs[1], program2)

    def test_should_reject_program_that_has_common_part_with_already_created_one(self):
        program1 = Program("1001", 2, 4, 16.5, 17.1)
        self.controller.create_program(program1)
        program2 = Program("1001", 1, 5, 16.1, 17.4)
        with self.assertRaises(ProgramError):
            self.controller.create_program(program2)
        program2 = Program("1002", 2, 5, 16.1, 17.4)
        with self.assertRaises(ProgramError):
            self.controller.create_program(program2)
        program2 = Program("1002", 1, 4, 16.1, 17.4)
        with self.assertRaises(ProgramError):
            self.controller.create_program(program2)

    def test_should_reject_program_that_has_invalid_therm_sensor_id(self):
        invalid_sensor_id = "invalid_sensor_id"
        program = Program(invalid_sensor_id, 2, 4, 16.5, 17.1)
        with self.assertRaises(ProgramError):
            self.controller.create_program(program)

    def test_should_reject_program_that_has_invalid_relay_index(self):
        # TODO add this
        pass
