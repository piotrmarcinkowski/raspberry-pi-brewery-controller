import unittest
from unittest.mock import Mock

from app.controller import Controller, ProgramError
from app.hardware.therm_sensor_api import ThermSensorApi, NoSensorFoundError, SensorNotReadyError
from app.program import Program
from app.hardware.relay_api import RelayApi
from app.storage import Storage


class StorageMock(Mock):
    def __init__(self, programs=[], sensors=[]):
        super().__init__(spec=Storage)
        self.store_sensors = Mock(side_effect=self.__store_sensors_mock)
        self.load_sensors = Mock(side_effect=self.__load_sensors_mock)
        self.store_programs = Mock(side_effect=self.__store_programs_mock)
        self.load_programs = Mock(side_effect=self.__load_programs_mock)
        self.__programs = programs
        self.__sensors = sensors

    def __load_sensors_mock(self):
        return self.__sensors

    def __store_sensors_mock(self, sensors):
        self.__sensors = sensors

    def __store_programs_mock(self, programs):
        self.__programs = programs

    def __load_programs_mock(self):
        return self.__programs


class ControllerTestCase(unittest.TestCase):
    MOCKED_SENSOR_IDS = ["1001", "1002", "1003", "1004"]
    MOCKED_SENSOR_TEMP = {"1001": 12.3, "1002": 23.4, "1003": 22.0, "1004": 19.4}

    def mock_get_sensor_temp(self, sensor_id):
        return self.MOCKED_SENSOR_TEMP[sensor_id]

    def setUp(self):
        self.therm_sensor_api_mock = Mock(spec=ThermSensorApi)
        self.therm_sensor_api_mock.get_sensor_id_list = Mock(return_value=self.MOCKED_SENSOR_IDS)
        self.therm_sensor_api_mock.get_sensor_temperature = Mock(side_effect=self.mock_get_sensor_temp)
        self.relay_api_mock = Mock(spec=RelayApi)
        self.storage_mock = StorageMock()
        self.controller = Controller(
            therm_sensor_api=self.therm_sensor_api_mock,
            relay_api=self.relay_api_mock,
            storage=self.storage_mock)

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
        self.storage_mock.store_programs.assert_called_with([program1])
        program2 = Program("1002", 1, 5, 16.1, 17.4)
        self.controller.create_program(program2)
        self.storage_mock.store_programs.assert_called_with([program1, program2])
        programs = self.controller.get_programs()
        self.assertEqual(programs[0], program1)
        self.assertEqual(programs[1], program2)

    def test_should_create_programs_with_given_parameters_cooling_only(self):
        program1 = Program("1001", -1, 4, 16.5, 17.1)
        self.controller.create_program(program1)
        self.storage_mock.store_programs.assert_called_with([program1])
        program2 = Program("1002", -1, 5, 16.1, 17.4)
        self.controller.create_program(program2)
        self.storage_mock.store_programs.assert_called_with([program1, program2])
        programs = self.controller.get_programs()
        self.assertEqual(programs[0], program1)
        self.assertEqual(programs[1], program2)

    def test_should_create_programs_with_given_parameters_heating_only(self):
        program1 = Program("1001", 2, -1, 16.5, 17.1)
        self.controller.create_program(program1)
        self.storage_mock.store_programs.assert_called_with([program1])
        program2 = Program("1002", 1, -1, 16.1, 17.4)
        self.controller.create_program(program2)
        self.storage_mock.store_programs.assert_called_with([program1, program2])
        programs = self.controller.get_programs()
        self.assertEqual(programs[0], program1)
        self.assertEqual(programs[1], program2)

    def test_should_reject_created_program_on_error_while_storing(self):
        program1 = Program("1001", 2, 4, 16.5, 17.1)
        self.controller.create_program(program1)
        program2 = Program("1002", 1, 5, 16.1, 17.4)
        self.storage_mock.store_programs = Mock(side_effect=IOError())
        with self.assertRaises(ProgramError):
            self.controller.create_program(program2)
        programs = self.controller.get_programs()
        self.assertEqual(programs[0], program1)

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
        program1 = Program("1001", -2, 4, 16.5, 17.1)
        with self.assertRaises(ProgramError):
            self.controller.create_program(program1)
        program2 = Program("1001", 3, -2, 16.5, 17.1)
        with self.assertRaises(ProgramError):
            self.controller.create_program(program2)
        program3 = Program("1001", Controller.RELAYS_COUNT, 0, 16.5, 17.1)
        with self.assertRaises(ProgramError):
            self.controller.create_program(program3)
        program4 = Program("1001", 0, Controller.RELAYS_COUNT, 16.5, 17.1)
        with self.assertRaises(ProgramError):
            self.controller.create_program(program4)

    def test_should_delete_existing_program_0(self):
        program1 = Program("1001", 2, 4, 16.5, 17.1)
        self.controller.create_program(program1)
        program2 = Program("1002", 1, 5, 16.1, 17.4)
        self.controller.create_program(program2)
        program3 = Program("1003", 3, 6, 16.0, 17.2)
        self.controller.create_program(program3)
        self.controller.delete_program(0)
        programs = self.controller.get_programs()
        self.assertEqual(programs[0], program2)
        self.assertEqual(programs[1], program3)
        self.assertFalse(program1.active)
        self.storage_mock.store_programs.assert_called_with(programs)

    def test_should_delete_existing_program_1(self):
        program1 = Program("1001", 2, 4, 16.5, 17.1)
        self.controller.create_program(program1)
        program2 = Program("1002", 1, 5, 16.1, 17.4)
        self.controller.create_program(program2)
        program3 = Program("1003", 3, 6, 16.0, 17.2)
        self.controller.create_program(program3)
        self.controller.delete_program(1)
        programs = self.controller.get_programs()
        self.assertEqual(programs[0], program1)
        self.assertEqual(programs[1], program3)
        self.assertFalse(program2.active)
        self.storage_mock.store_programs.assert_called_with(programs)

    def test_should_delete_existing_program_2(self):
        program1 = Program("1001", 2, 4, 16.5, 17.1)
        self.controller.create_program(program1)
        program2 = Program("1002", 1, 5, 16.1, 17.4)
        self.controller.create_program(program2)
        program3 = Program("1003", 3, 6, 16.0, 17.2)
        self.controller.create_program(program3)
        self.controller.delete_program(2)
        programs = self.controller.get_programs()
        self.assertEqual(programs[0], program1)
        self.assertEqual(programs[1], program2)
        self.assertFalse(program3.active)
        self.storage_mock.store_programs.assert_called_with(programs)

    def test_should_raise_when_deleting_program_with_invalid_index(self):
        program1 = Program("1001", 2, 4, 16.5, 17.1)
        self.controller.create_program(program1)
        program2 = Program("1002", 1, 5, 16.1, 17.4)
        self.controller.create_program(program2)
        program3 = Program("1003", 3, 6, 16.0, 17.2)
        self.controller.create_program(program3)
        with self.assertRaises(ProgramError):
            self.controller.delete_program(-1)
        with self.assertRaises(ProgramError):
            self.controller.delete_program(3)
        with self.assertRaises(ProgramError):
            self.controller.delete_program(99)
        programs = self.controller.get_programs()
        self.assertEqual(programs[0], program1)
        self.assertEqual(programs[1], program2)
        self.assertEqual(programs[2], program3)

    def test_should_leave_programs_intact_on_error_while_saving_after_delete(self):
        program1 = Program("1001", 2, 4, 16.5, 17.1)
        self.controller.create_program(program1)
        program2 = Program("1002", 1, 5, 16.1, 17.4)
        self.controller.create_program(program2)
        program3 = Program("1003", 3, 6, 16.0, 17.2)
        self.controller.create_program(program3)
        self.storage_mock.store_programs = Mock(side_effect=IOError())
        with self.assertRaises(ProgramError):
            self.controller.delete_program(0)
        programs = self.controller.get_programs()
        self.assertEqual(programs[0], program1)
        self.assertEqual(programs[1], program2)
        self.assertEqual(programs[2], program3)

    def test_should_modify_program_with_given_index(self):
        program1 = Program("1001", 2, 4, 16.5, 17.1)
        self.controller.create_program(program1)
        program2 = Program("1002", 1, 5, 16.1, 17.4)
        self.controller.create_program(program2)
        program3 = Program("1003", 3, 6, 16.0, 17.2)
        self.controller.create_program(program3)
        modified_program2 = Program("1004", 0, 7, 15.8, 15.9, False)
        self.controller.modify_program(1, modified_program2)
        programs = self.controller.get_programs()
        self.storage_mock.store_programs.assert_called_with(programs)
        self.assertEqual(programs[0], program1)
        self.assertEqual(programs[1], modified_program2)
        self.assertEqual(programs[2], program3)

    def test_should_reject_modified_program_on_error_while_storing(self):
        program1 = Program("1001", 2, 4, 16.5, 17.1)
        self.controller.create_program(program1)
        program2 = Program("1002", 1, 5, 16.1, 17.4)
        self.controller.create_program(program2)
        program3 = Program("1003", 3, 6, 16.0, 17.2)
        self.controller.create_program(program3)
        modified_program2 = Program("1004", 0, 7, 15.8, 15.9, False)
        self.storage_mock.store_programs = Mock(side_effect=IOError())
        with self.assertRaises(ProgramError):
            self.controller.modify_program(1, modified_program2)
        programs = self.controller.get_programs()
        self.assertEqual(programs[0], program1)
        self.assertEqual(programs[1], program2)
        self.assertEqual(programs[2], program3)

    def test_should_raise_if_modifying_program_with_invalid_index(self):
        program1 = Program("1001", 2, 4, 16.5, 17.1)
        with self.assertRaises(ProgramError):
            self.controller.modify_program(0, program1)
        self.controller.create_program(program1)
        program2 = Program("1002", 1, 5, 16.1, 17.4)
        self.controller.create_program(program2)
        program3 = Program("1003", 3, 6, 16.0, 17.2)
        self.controller.create_program(program3)
        modified_program2 = Program("1004", 0, 7, 15.8, 15.9, False)
        with self.assertRaises(ProgramError):
            self.controller.modify_program(-1, modified_program2)
        with self.assertRaises(ProgramError):
            self.controller.modify_program(3, modified_program2)
        programs = self.controller.get_programs()
        self.assertEqual(programs[0], program1)
        self.assertEqual(programs[1], program2)
        self.assertEqual(programs[2], program3)

    def test_should_raise_if_program_modification_collides_with_other_program(self):
        program1 = Program("1001", 2, 4, 16.5, 17.1)
        self.controller.create_program(program1)
        program2 = Program("1002", 1, 5, 16.1, 17.4)
        self.controller.create_program(program2)
        program3 = Program("1003", 3, 6, 16.0, 17.2)
        self.controller.create_program(program3)
        modified_program2 = Program("1003", 0, 7, 15.8, 15.9, False)
        with self.assertRaises(ProgramError):
            self.controller.modify_program(1, modified_program2)
        modified_program2 = Program("1002", 2, 7, 15.2, 15.3, False)
        with self.assertRaises(ProgramError):
            self.controller.modify_program(1, modified_program2)
        modified_program2 = Program("1002", 1, 6, 15.4, 15.5, False)
        with self.assertRaises(ProgramError):
            self.controller.modify_program(1, modified_program2)
        programs = self.controller.get_programs()
        self.assertEqual(programs[0], program1)
        self.assertEqual(programs[1], program2)
        self.assertEqual(programs[2], program3)

    def test_should_load_programs_and_start_updating_them_when_run(self):
        program1 = Mock(spec=Program)
        program2 = Mock(spec=Program)
        program3 = Mock(spec=Program)
        self.storage_mock = StorageMock(programs=[program1, program2, program3])

        main_loop_exit_condition = TestLoopExitCondition()

        self.controller = Controller(
            therm_sensor_api=self.therm_sensor_api_mock,
            relay_api=self.relay_api_mock,
            storage=self.storage_mock)

        self.controller.run(
            interval_secs=0.01,
            main_loop_exit_condition=main_loop_exit_condition.should_exit_main_loop)

        program1.update.assert_called_with()
        program2.update.assert_called_with()
        program3.update.assert_called_with()

    def test_should_start_updating_created_program(self):
        program = Mock(spec=Program)
        program.sensor_id = "1001"
        program.cooling_relay_index = 1
        program.heating_relay_index = 2
        program.min_temperature = 18
        program.max_temperature = 19

        # the following task will be run on iteration 2, simulating program creation
        create_program_task = CreateProgramTask(2, self.controller, program)
        main_loop_exit_condition = TestLoopExitCondition(max_iterations=3)
        main_loop_exit_condition.add_task(create_program_task)

        self.controller.run(
            interval_secs=0.01,
            main_loop_exit_condition=main_loop_exit_condition.should_exit_main_loop)

        # test if program gets updated after being added to controller
        program.update.assert_called_with()

    def test_should_reject_sensor_name_change_for_non_existing_sensor(self):
        with self.assertRaises(NoSensorFoundError):
            self.controller.set_therm_sensor_name("invalid_sensor_id", "sensor_name")

    def test_should_set_sensor_name_and_return_modified_sensor(self):
        sensor = self.controller.set_therm_sensor_name(self.MOCKED_SENSOR_IDS[0], "sensor_name")
        self.assertEqual(sensor.id, self.MOCKED_SENSOR_IDS[0])
        self.assertEqual(sensor.name, "sensor_name")

    def test_returned_sensor_list_should_contain_sensor_with_modified_name(self):
        sensor = self.controller.set_therm_sensor_name("1001", "sensor_name")
        self.assertTrue(sensor in self.controller.get_therm_sensors())


class IterationTask:
    """
    Class implements simple task that gets run at controller iteration. See TestLoopExitCondition
    :param iteration: Iteration at which the task will be executed
    :type iteration: int
    """
    def __init__(self, iteration):
        self.iteration = iteration

    def run(self):
        pass


class CreateProgramTask(IterationTask):
    """
    Task that adds  a program to controller.
    """
    def __init__(self, iteration, controller, program):
        super(CreateProgramTask, self).__init__(iteration)
        self.__controller = controller
        self.__program = program

    def run(self):
        self.__controller.create_program(self.__program)


class TestLoopExitCondition:
    """
    Gets passed to controller's run method as a replacement of default method for checking if controller should
    terminate. Additionally tasks can be added that will be called upon iterations simulating changes to controller
    after it has been started
    """
    def __init__(self, max_iterations=1) -> None:
        super().__init__()
        self.__iteration = 0
        self.__max_iterations = max_iterations
        self.__iteration_tasks = []

    def should_exit_main_loop(self):
        """
        Method called at each iteration checking if controller should terminate. For test purposes it also does
        additional things like running tasks
        :return:
        """
        should_exit = self.__iteration >= self.__max_iterations
        self.__iteration += 1
        for task in self.__iteration_tasks:
            # check if the task is for this iteration and run it
            if task.iteration == self.__iteration:
                task.run()
        return should_exit

    def add_task(self, iteration_task):
        """
        Adds a task that's going to be executed at specified iteration
        :param iteration_task: task to execute
        """
        self.__iteration_tasks.append(iteration_task)
