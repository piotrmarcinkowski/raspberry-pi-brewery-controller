import unittest
from unittest.mock import Mock, call

from app.controller import Controller, ProgramError
from app.hardware.therm_sensor_api import ThermSensorApi, NoSensorFoundError, SensorNotReadyError
from app.program import Program
from tests.mocks import StorageMock, ThermSensorApiMock, RelayApiMock

PROGRAM_NAME = "ProgramName"
PROGRAM_CRC = "CRC"


def create_test_program(sensor_id, heating_relay_index, cooling_relay_index,
                        min_temperature, max_temperature, active=True, program_id=Program.UNDEFINED_ID):
    return Program(program_id, PROGRAM_NAME,
                   sensor_id, heating_relay_index, cooling_relay_index, min_temperature, max_temperature, active)


class ControllerTestCase(unittest.TestCase):
    MOCKED_SENSOR_IDS = ["1001", "1002", "1003", "1004"]
    MOCKED_SENSOR_TEMP = {"1001": 12.3, "1002": 23.4, "1003": 22.0, "1004": 19.4}

    def setUp(self):
        self.therm_sensor_api_mock = ThermSensorApiMock()
        self.therm_sensor_api_mock.mock_sensors(ControllerTestCase.MOCKED_SENSOR_IDS)
        self.therm_sensor_api_mock.mock_sensors_temperature(ControllerTestCase.MOCKED_SENSOR_TEMP)
        self.relay_api_mock = RelayApiMock()
        self.storage_mock = StorageMock()
        self.controller = Controller(
            therm_sensor_api=self.therm_sensor_api_mock,
            relay_api=self.relay_api_mock,
            storage=self.storage_mock)

    def add_test_program(self, sensor_id, heating_relay_index, cooling_relay_index,
                         min_temperature, max_temperature, active=True):
        return self.controller.create_program(
            create_test_program(sensor_id, heating_relay_index, cooling_relay_index,
                                min_temperature, max_temperature, active))

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
        program1 = self.add_test_program("1001", 2, 4, 16.5, 17.1)
        self.storage_mock.store_programs.assert_called_with([program1])
        program2 = self.add_test_program("1002", 1, 5, 16.1, 17.4)
        self.storage_mock.store_programs.assert_called_with([program1, program2])
        programs = self.controller.get_programs()
        self.assertEqual(programs[0], program1)
        self.assertEqual(programs[1], program2)

    def test_should_create_programs_with_given_parameters_cooling_only(self):
        program1 = self.add_test_program("1001", -1, 4, 16.5, 17.1)
        self.storage_mock.store_programs.assert_called_with([program1])
        program2 = self.add_test_program("1002", -1, 5, 16.1, 17.4)
        self.storage_mock.store_programs.assert_called_with([program1, program2])
        programs = self.controller.get_programs()
        self.assertEqual(programs[0], program1)
        self.assertEqual(programs[1], program2)

    def test_should_create_programs_with_given_parameters_heating_only(self):
        program1 = self.add_test_program("1001", 2, -1, 16.5, 17.1)
        self.storage_mock.store_programs.assert_called_with([program1])
        program2 = self.add_test_program("1002", 1, -1, 16.1, 17.4)
        self.storage_mock.store_programs.assert_called_with([program1, program2])
        programs = self.controller.get_programs()
        self.assertEqual(programs[0], program1)
        self.assertEqual(programs[1], program2)

    def test_should_reject_created_program_on_error_while_storing(self):
        program1 = self.add_test_program("1001", 2, 4, 16.5, 17.1)
        program2 = create_test_program("1002", 1, 5, 16.1, 17.4)
        self.storage_mock.store_programs = Mock(side_effect=IOError())
        with self.assertRaises(ProgramError):
            self.controller.create_program(program2)
        programs = self.controller.get_programs()
        self.assertEqual(1, len(programs))
        self.assertEqual(programs[0], program1)

    def test_should_reject_program_that_has_common_part_with_already_created_one(self):
        program1 = self.add_test_program("1001", 2, 4, 16.5, 17.1)
        program2 = create_test_program("1001", 1, 5, 16.1, 17.4)
        with self.assertRaises(ProgramError):
            self.controller.create_program(program2)
        program2 = create_test_program("1002", 2, 5, 16.1, 17.4)
        with self.assertRaises(ProgramError):
            self.controller.create_program(program2)
        program2 = create_test_program("1002", 1, 4, 16.1, 17.4)
        with self.assertRaises(ProgramError):
            self.controller.create_program(program2)

    def test_should_reject_program_that_has_invalid_therm_sensor_id(self):
        invalid_sensor_id = "invalid_sensor_id"
        program = create_test_program(invalid_sensor_id, 2, 4, 16.5, 17.1)
        with self.assertRaises(ProgramError):
            self.controller.create_program(program)

    def test_should_reject_program_that_has_invalid_relay_index(self):
        program1 = create_test_program("1001", -2, 4, 16.5, 17.1)
        with self.assertRaises(ProgramError):
            self.controller.create_program(program1)
        program2 = create_test_program("1001", 3, -2, 16.5, 17.1)
        with self.assertRaises(ProgramError):
            self.controller.create_program(program2)
        program3 = create_test_program("1001", Controller.RELAYS_COUNT, 0, 16.5, 17.1)
        with self.assertRaises(ProgramError):
            self.controller.create_program(program3)
        program4 = create_test_program("1001", 0, Controller.RELAYS_COUNT, 16.5, 17.1)
        with self.assertRaises(ProgramError):
            self.controller.create_program(program4)

    def test_should_delete_existing_program_0(self):
        program1 = self.add_test_program("1001", 2, 4, 16.5, 17.1)
        program2 = self.add_test_program("1002", 1, 5, 16.1, 17.4)
        program3 = self.add_test_program("1003", 3, 6, 16.0, 17.2)
        self.controller.delete_program(program1.program_id)
        programs = self.controller.get_programs()
        self.assertEqual(programs[0], program2)
        self.assertEqual(programs[1], program3)
        self.storage_mock.store_programs.assert_called_with(programs)

    def test_should_delete_existing_program_1(self):
        program1 = self.add_test_program("1001", 2, 4, 16.5, 17.1)
        program2 = self.add_test_program("1002", 1, 5, 16.1, 17.4)
        program3 = self.add_test_program("1003", 3, 6, 16.0, 17.2)
        self.controller.delete_program(program2.program_id)
        programs = self.controller.get_programs()
        self.assertEqual(programs[0], program1)
        self.assertEqual(programs[1], program3)
        self.storage_mock.store_programs.assert_called_with(programs)

    def test_should_delete_existing_program_2(self):
        program1 = self.add_test_program("1001", 2, 4, 16.5, 17.1)
        program2 = self.add_test_program("1002", 1, 5, 16.1, 17.4)
        program3 = self.add_test_program("1003", 3, 6, 16.0, 17.2)
        self.controller.delete_program(program3.program_id)
        programs = self.controller.get_programs()
        self.assertEqual(programs[0], program1)
        self.assertEqual(programs[1], program2)
        self.storage_mock.store_programs.assert_called_with(programs)

    def test_should_raise_when_deleting_program_with_invalid_index(self):
        program1 = self.add_test_program("1001", 2, 4, 16.5, 17.1)
        program2 = self.add_test_program("1002", 1, 5, 16.1, 17.4)
        program3 = self.add_test_program("1003", 3, 6, 16.0, 17.2)
        self.controller.delete_program(program1.program_id)
        with self.assertRaises(ProgramError):
            self.controller.delete_program(program1)
        programs = self.controller.get_programs()
        self.assertEqual(programs[0], program2)
        self.assertEqual(programs[1], program3)

    def test_should_leave_programs_intact_on_error_while_saving_after_delete(self):
        program1 = self.add_test_program("1001", 2, 4, 16.5, 17.1)
        program2 = self.add_test_program("1002", 1, 5, 16.1, 17.4)
        program3 = self.add_test_program("1003", 3, 6, 16.0, 17.2)
        self.storage_mock.store_programs = Mock(side_effect=IOError())
        with self.assertRaises(ProgramError):
            self.controller.delete_program(program1)
        programs = self.controller.get_programs()
        self.assertEqual(programs[0], program1)
        self.assertEqual(programs[1], program2)
        self.assertEqual(programs[2], program3)

    def test_should_modify_program_with_given_id(self):
        program1 = self.add_test_program("1001", 2, 4, 16.5, 17.1)
        program2 = self.add_test_program("1002", 1, 5, 16.1, 17.4)
        program3 = self.add_test_program("1003", 3, 6, 16.0, 17.2)
        modified_program2 = create_test_program("1004", 0, 7, 15.8, 15.9, False, program2.program_id)
        self.controller.modify_program(program2.program_id, modified_program2)
        programs = self.controller.get_programs()
        self.storage_mock.store_programs.assert_called_with(programs)
        self.assertEqual(programs[0], program1)
        self.assertEqual(modified_program2, programs[1])
        self.assertEqual(programs[2], program3)

    def test_should_reject_modified_program_on_error_while_storing(self):
        program1 = self.add_test_program("1001", 2, 4, 16.5, 17.1)
        program2 = self.add_test_program("1002", 1, 5, 16.1, 17.4)
        program3 = self.add_test_program("1003", 3, 6, 16.0, 17.2)
        modified_program2 = create_test_program("1004", 0, 7, 15.8, 15.9, False, program2.program_id)
        self.storage_mock.store_programs = Mock(side_effect=IOError())
        with self.assertRaises(ProgramError):
            self.controller.modify_program(program2.program_id, modified_program2)
        programs = self.controller.get_programs()
        self.assertEqual(programs[0], program1)
        self.assertEqual(programs[1], program2)
        self.assertEqual(programs[2], program3)

    def test_should_raise_if_modifying_program_with_invalid_id(self):
        program1 = create_test_program("1001", 2, 4, 16.5, 17.1)
        with self.assertRaises(ProgramError):
            self.controller.modify_program(program1.program_id, program1)
        program1 = self.controller.create_program(program1)
        program2 = self.add_test_program("1002", 1, 5, 16.1, 17.4)
        program3 = self.add_test_program("1003", 3, 6, 16.0, 17.2)
        self.controller.delete_program(program2.program_id)
        modified_program2 = create_test_program("1004", 0, 7, 15.8, 15.9, False, program2.program_id)
        with self.assertRaises(ProgramError):
            self.controller.modify_program(program2.program_id, modified_program2)
        with self.assertRaises(ProgramError):
            self.controller.modify_program(program2.program_id, modified_program2)
        programs = self.controller.get_programs()
        self.assertEqual(programs[0], program1)
        self.assertEqual(programs[1], program3)

    def test_should_raise_if_program_modification_collides_with_other_program(self):
        program1 = self.add_test_program("1001", 2, 4, 16.5, 17.1)
        program2 = self.add_test_program("1002", 1, 5, 16.1, 17.4)
        program3 = self.add_test_program("1003", 3, 6, 16.0, 17.2)
        modified_program2 = create_test_program("1003", 0, 7, 15.8, 15.9, False, program2.program_id)
        with self.assertRaises(ProgramError):
            self.controller.modify_program(program2.program_id, modified_program2)
        modified_program2 = create_test_program("1002", 2, 7, 15.2, 15.3, False, program2.program_id)
        with self.assertRaises(ProgramError):
            self.controller.modify_program(program2.program_id, modified_program2)
        modified_program2 = create_test_program("1002", 1, 6, 15.4, 15.5, False, program2.program_id)
        with self.assertRaises(ProgramError):
            self.controller.modify_program(program2.program_id, modified_program2)
        programs = self.controller.get_programs()
        self.assertEqual(programs[0], program1)
        self.assertEqual(programs[1], program2)
        self.assertEqual(programs[2], program3)

    def test_should_load_programs_and_start_monitoring_when_run(self):
        program1 = create_test_program("1001", 2, 4, 2.0, 3.0, program_id="id1")  # cooling should get activated
        program2 = create_test_program("1002", 1, 5, 25.0, 28.0, program_id="id2")  # heating should get activated
        program3 = create_test_program("1003", 3, 6, 0.0, 30.0, program_id="id3")  # no action needed
        self.storage_mock = StorageMock(programs=[program1, program2, program3])

        main_loop_exit_condition = TestLoopExitCondition()

        self.controller = Controller(
            therm_sensor_api=self.therm_sensor_api_mock,
            relay_api=self.relay_api_mock,
            storage=self.storage_mock)

        self.controller.run(
            interval_secs=0.01,
            main_loop_exit_condition=main_loop_exit_condition.should_exit_main_loop)

        calls = [call(4, 1), call(1, 1)]
        self.relay_api_mock.set_relay_state.assert_has_calls(calls, any_order=True)

    def test_should_throw_if_stored_programs_are_incomplete(self):
        program1 = create_test_program("1001", 2, 4, 2.0, 3.0, program_id="program_id")
        program2 = create_test_program("1002", 1, 5, 25.0, 28.0)  # program with no id
        self.storage_mock = StorageMock(programs=[program1, program2])

        main_loop_exit_condition = TestLoopExitCondition()

        self.controller = Controller(
            therm_sensor_api=self.therm_sensor_api_mock,
            relay_api=self.relay_api_mock,
            storage=self.storage_mock)

        with self.assertRaises(ProgramError):
            self.controller.run(
                interval_secs=0.01,
                main_loop_exit_condition=main_loop_exit_condition.should_exit_main_loop)

    def test_should_start_monitor_created_program(self):
        program = create_test_program("1001", 2, 4, 2.0, 3.0)  # cooling should get activated

        # the following task will be run on iteration 2, simulating program creation
        create_program_task = CreateProgramTask(2, self.controller, program)
        main_loop_exit_condition = TestLoopExitCondition(max_iterations=3)
        main_loop_exit_condition.add_task(create_program_task)

        self.controller.run(
            interval_secs=0.01,
            main_loop_exit_condition=main_loop_exit_condition.should_exit_main_loop)

        # test if program gets updated after being added to controller
        self.relay_api_mock.set_relay_state.assert_called_with(4, 1)

    def test_should_deactivate_old_heating_relay_if_it_has_been_modified_for_a_program(self):
        self.therm_sensor_api_mock.mock_sensors_temperature({"1001": 9.0})
        program = self.add_test_program("1001", 1, -1, 10.0, 12.0)  # heating should get activated
        # change heating relay
        modified_program = program.modify_with(program, heating_relay_index=2)

        modify_program_task = ModifyProgramTask(3, self.controller, modified_program)
        main_loop_exit_condition = TestLoopExitCondition(max_iterations=3)
        main_loop_exit_condition.add_task(modify_program_task)

        self.controller.run(
            interval_secs=0.01,
            main_loop_exit_condition=main_loop_exit_condition.should_exit_main_loop)

        # test if after program was modified by changing it's cooling relay the old relay gets deactivated
        calls = [call(1, 1), call(1, 0), call(2, 1)]
        self.assertEqual(calls, self.relay_api_mock.set_relay_state.mock_calls)

    def test_should_deactivate_old_cooling_relay_if_it_has_been_modified_for_a_program(self):
        self.therm_sensor_api_mock.mock_sensors_temperature({"1001": 13.0})
        program = self.add_test_program("1001", -1, 1, 10.0, 12.0)  # cooling should get activated
        # change cooling relay
        modified_program = program.modify_with(program, cooling_relay_index=2)

        modify_program_task = ModifyProgramTask(3, self.controller, modified_program)
        main_loop_exit_condition = TestLoopExitCondition(max_iterations=3)
        main_loop_exit_condition.add_task(modify_program_task)

        self.controller.run(
            interval_secs=0.01,
            main_loop_exit_condition=main_loop_exit_condition.should_exit_main_loop)

        # test if after program was modified by changing it's cooling relay the old relay gets deactivated
        calls = [call(1, 1), call(1, 0), call(2, 1)]
        self.assertEqual(calls, self.relay_api_mock.set_relay_state.mock_calls)

    def test_should_activate_relays_for_multiple_programs(self):
        self.therm_sensor_api_mock.mock_sensors_temperature({"1001": 13.0, "1002": 13.0})
        program1 = self.add_test_program("1001", -1, 1, 10.0, 12.0)  # cooling should get activated
        program2 = self.add_test_program("1002", -1, 2, 10.0, 12.0)  # cooling should get activated

        main_loop_exit_condition = TestLoopExitCondition(max_iterations=3)
        self.controller.run(
            interval_secs=0.01,
            main_loop_exit_condition=main_loop_exit_condition.should_exit_main_loop)

        calls = [call(1, 1), call(2, 1)]
        self.assertEqual(calls, self.relay_api_mock.set_relay_state.mock_calls)

    def test_should_deactivate_unassigned_relays(self):
        self.therm_sensor_api_mock.mock_sensors_temperature({"1001": 13.0, "1002": 13.0})
        self.relay_api_mock.mock_relay_state(5, 1)
        program1 = self.add_test_program("1001", -1, 1, 10.0, 12.0)  # cooling should get activated
        program2 = self.add_test_program("1002", -1, 2, 10.0, 12.0)  # cooling should get activated

        main_loop_exit_condition = TestLoopExitCondition(max_iterations=3)
        self.controller.run(
            interval_secs=0.01,
            main_loop_exit_condition=main_loop_exit_condition.should_exit_main_loop)

        calls = [call(5, 0), call(1, 1), call(2, 1)]
        self.assertEqual(calls, self.relay_api_mock.set_relay_state.mock_calls)

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

    def test_should_return_state_for_given_program(self):
        self.therm_sensor_api_mock.mock_sensors_temperature({"1001": 13.0})
        program = self.add_test_program("1001", -1, 1, 10.0, 12.0)

        state = self.controller.get_program_state(program.program_id)

        self.assertEqual(program.program_id, state.program_id)
        self.assertIsNotNone(state.program_crc)
        self.assertIsNotNone(state.cooling_activated)
        self.assertIsNotNone(state.heating_activated)
        self.assertIsNotNone(state.current_temperature)

    def test_should_return_states_for_all_programs(self):
        self.therm_sensor_api_mock.mock_sensors_temperature({"1001": 13.0, "1002": 14.0})
        program1 = self.add_test_program("1001", -1, 1, 10.0, 12.0)
        program2 = self.add_test_program("1002", 1, -1, 15.0, 16.0)

        states = self.controller.get_program_states()

        self.assertEqual(program1.program_id, states[0].program_id)
        self.assertEqual(program2.program_id, states[1].program_id)


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
    Task that adds a program to controller.
    """
    def __init__(self, iteration, controller, program):
        super(CreateProgramTask, self).__init__(iteration)
        self.__controller = controller
        self.__program = program

    def run(self):
        self.__controller.create_program(self.__program)


class ModifyProgramTask(IterationTask):
    """
    Task that modifies existing program.
    """
    def __init__(self, iteration, controller, program):
        super(ModifyProgramTask, self).__init__(iteration)
        self.__controller = controller
        self.__program = program

    def run(self):
        self.__controller.modify_program(self.__program.program_id, self.__program)


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
