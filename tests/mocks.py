from unittest.mock import Mock
import uuid

from app.controller import Controller, ProgramError
from app.hardware.therm_sensor_api import SensorNotReadyError, NoSensorFoundError, ThermSensorApi
from app.hardware.relay_api import RelayApi
from app.program import Program
from app.storage import Storage
from therm_sensor import ThermSensor


class ThermSensorApiMock(Mock):
    MOCKED_NOT_READY_SENSOR_ID = "not_ready_sensor"
    MOCKED_SENSORS = ["1001", "1002", "1003", "1004"]
    MOCKED_SENSORS_TEMPERATURE = {
        "1001": 20.123,
        "1002": 19.234,
        "1003": 18.345,
        "1004": 15.0
    }

    def __init__(self):
        super().__init__(spec=ThermSensorApi)
        self.sensors = []
        self.temperatures = {}
        self.get_sensor_id_list = Mock(side_effect=self.__mocked_get_sensor_id_list)
        self.get_sensor_temperature = Mock(side_effect=self.__mocked_get_sensor_temperature)
        self.mock_sensors(ThermSensorApiMock.MOCKED_SENSORS)
        self.mock_sensors_temperature(ThermSensorApiMock.MOCKED_SENSORS_TEMPERATURE)

    def mock_sensors(self, sensors):
        self.sensors = sensors

    def mock_sensors_temperature(self, temperatures):
        self.temperatures = temperatures

    def __mocked_get_sensor_id_list(self):
        return self.sensors

    def __mocked_get_sensor_temperature(self, sensor_id):
        if sensor_id == self.MOCKED_NOT_READY_SENSOR_ID:
            raise SensorNotReadyError(sensor_id)
        if sensor_id in self.temperatures:
            temperature = self.temperatures[sensor_id]
            if temperature is None:
                raise SensorNotReadyError(sensor_id)
            return temperature
        else:
            raise NoSensorFoundError(sensor_id)


class RelayApiMock(Mock):
    def __init__(self):
        super().__init__(spec=RelayApi)
        self.relays = {relay_index: 0 for relay_index in range(len(RelayApi.RELAY_GPIO_CHANNELS))}
        self.get_relay_state = Mock(side_effect=self.__get_relay_state)
        self.set_relay_state = Mock(side_effect=self.__set_relay_state)

    def mock_relay_state(self, relay_index, state):
        self.relays[relay_index] = state

    def __get_relay_state(self, relay_index):
        return self.relays[relay_index]

    def __set_relay_state(self, relay_index, relay_state):
        self.relays[relay_index] = relay_state


class ControllerMock(Mock):
    DEFAULT_ERROR_MESSAGE = "Error message"

    def __init__(self):
        super().__init__(spec=Controller)

        self.therm_sensor_api = ThermSensorApiMock()
        self.relay_api = RelayApiMock()

        self.get_therm_sensors = Mock(side_effect=self.__mocked_get_sensors)
        self.get_therm_sensor_temperature = Mock(side_effect=self.therm_sensor_api.get_sensor_temperature)
        self.create_program = Mock(side_effect=self.__mocked_create_program)
        self.modify_program = Mock(side_effect=self.__mocked_modify_program)
        self.delete_program = Mock(side_effect=self.__mocked_delete_program)
        self.get_programs = Mock(side_effect=self.__mocked_get_programs)
        self.get_program_state = Mock(side_effect=self.__mocked_get_program_state)
        self.get_program_states = Mock(side_effect=self.__mocked_get_program_states)

        self.programs = []
        self.__next_program_id = None
        self.__temperatures = {}

    def get_next_program_id(self):
        if self.__next_program_id is None:
            self.__generate_next_program_id()
        return self.__next_program_id

    def raise_error_on_program_create(self):
        self.create_program = Mock(side_effect=ProgramError(message=ControllerMock.DEFAULT_ERROR_MESSAGE))

    def raise_error_on_program_modify(self):
        self.modify_program = Mock(side_effect=ProgramError(message=ControllerMock.DEFAULT_ERROR_MESSAGE))

    def raise_error_on_program_delete(self):
        self.delete_program = Mock(side_effect=ProgramError(message=ControllerMock.DEFAULT_ERROR_MESSAGE))

    def set_sensor_temperature(self, sensor_id, temperature):
        self.therm_sensor_api.temperatures[sensor_id] = temperature

    def set_relay_state(self, relay_index, relay_state):
        self.relay_api.relays[relay_index] = relay_state

    def __mocked_get_sensors(self):
        return [ThermSensor(sensor_id, "") for sensor_id in self.therm_sensor_api.get_sensor_id_list()]

    def __mocked_create_program(self, program):
        new_program = Program(
            program_id=self.get_next_program_id(),
            program_name=program.program_name,
            sensor_id=program.sensor_id,
            heating_relay_index=program.heating_relay_index,
            cooling_relay_index=program.cooling_relay_index,
            min_temperature=program.min_temperature,
            max_temperature=program.max_temperature,
            active=program.active)
        self.programs.append(new_program)
        self.__generate_next_program_id()
        return new_program

    def __mocked_modify_program(self, program_id, program):
        program_index = -1
        for index in range(len(self.programs)):
            if program_id == self.programs[index].program_id:
                program_index = index
                break
        if program_index < 0:
            raise ProgramError(program=program, message="Program with the given ID not found:{}".format(program.program_id),
                               error_code=ProgramError.ERROR_CODE_INVALID_ID)
        existing_program = self.programs[program_index]
        self.programs[program_index] = existing_program.modify_with(program)
        return self.programs[program_index]

    def __mocked_delete_program(self, program_id):
        program_index = -1
        for index in range(len(self.programs)):
            if program_id == self.programs[index].program_id:
                program_index = index
                break
        if program_index < 0:
            raise ProgramError(None, "Program with the given ID not found:{}".format(program_id),
                               ProgramError.ERROR_CODE_INVALID_ID)
        deleted_program = self.programs[program_index]
        del self.programs[program_index]
        return deleted_program

    def __mocked_get_programs(self):
        return self.programs

    def __generate_next_program_id(self):
        self.__next_program_id = str(uuid.uuid4())
        self.next_program_id = self.__next_program_id
        return self.__next_program_id

    def __mocked_get_program_state(self, program_id):
        program = self.__get_program_by_id(program_id)
        return program.create_program_state(self.therm_sensor_api, self.relay_api)

    def __mocked_get_program_states(self):
        return [self.programs[index].create_program_state(self.therm_sensor_api, self.relay_api)
                for index in range(len(self.programs))]

    def __get_program_by_id(self, program_id):
        for index in range(len(self.programs)):
            if program_id == self.programs[index].program_id:
                return self.programs[index]
        return None


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