from unittest.mock import Mock
import uuid

from app.controller import Controller, ProgramError
from app.hardware.therm_sensor_api import SensorNotReadyError, NoSensorFoundError, ThermSensorApi
from app.hardware.relay_api import RelayApi
from app.program import Program
from app.storage import Storage


class ThermSensorApiMock(Mock):
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
        super().__init__(spec=ThermSensorApi)
        self.__prepare_sensor_list()
        self.get_sensor_id_list = Mock(side_effect=self.__mocked_get_sensor_id_list)
        self.get_sensor_temperature = Mock(side_effect=self.__mocked_get_sensor_temperature)
        self.temperatures = {sensor_id: self.MOCKED_SENSORS_TEMPERATURE[sensor_id] for sensor_id in
                             self.MOCKED_SENSORS_TEMPERATURE}

    def __mocked_get_sensor_id_list(self):
        return self.sensor_mock_list

    def __mocked_get_sensor_temperature(self, sensor_id):
        if sensor_id == self.MOCKED_NOT_READY_SENSOR_ID:
            raise SensorNotReadyError(sensor_id)
        if sensor_id in ThermSensorApiMock.MOCKED_SENSORS_TEMPERATURE:
            return self.temperatures[sensor_id]
        else:
            raise NoSensorFoundError(sensor_id)

    def __prepare_sensor_list(self):
        self.sensor_mock_list = []
        for sensor_data in self.MOCKED_SENSORS:
            sensor_mock = Mock()
            sensor_mock.id = sensor_data["id"]
            sensor_mock.name = sensor_data["name"]
            self.sensor_mock_list.append(sensor_mock)


class RelayApiMock(Mock):
    def __init__(self):
        super().__init__(spec=RelayApi)
        self.relays = {relay_index: 0 for relay_index in range(len(RelayApi.RELAY_GPIO_CHANNELS))}
        self.get_relay_state = Mock(side_effect=self.__get_relay_state)

    def __get_relay_state(self, relay_index):
        return self.relays[relay_index]


class ControllerMock(Mock):
    DEFAULT_ERROR_MESSAGE = "Error message"

    def __init__(self):
        super().__init__(spec=Controller)

        self.therm_sensor_api = ThermSensorApiMock()
        ThermSensorApi.instance = Mock(return_value=self.therm_sensor_api)
        self.relay_api = RelayApiMock()
        RelayApi.instance = Mock(return_value=self.relay_api)

        self.get_therm_sensors = Mock(side_effect=self.therm_sensor_api.get_sensor_id_list)
        self.get_therm_sensor_temperature = Mock(side_effect=self.therm_sensor_api.get_sensor_temperature)
        self.create_program = Mock(side_effect=self.__mocked_create_program)
        self.modify_program = Mock(side_effect=self.__mocked_modify_program)
        self.delete_program = Mock(side_effect=self.__mocked_delete_program)
        self.get_programs = Mock(side_effect=self.__mocked_get_programs)
        self.get_program_state = Mock(side_effect=self.__mocked_get_program_state)

        self.programs = []
        self.__next_program_id = None
        self.__temperatures = {}

    def get_next_program_id(self):
        if self.__next_program_id is None:
            self.__generate_next_program_id()
        return self.__next_program_id

    def raise_error_on_program_create(self):
        self.create_program = Mock(side_effect=ProgramError(ControllerMock.DEFAULT_ERROR_MESSAGE))

    def raise_error_on_program_modify(self):
        self.modify_program = Mock(side_effect=ProgramError(ControllerMock.DEFAULT_ERROR_MESSAGE))

    def raise_error_on_program_delete(self):
        self.delete_program = Mock(side_effect=ProgramError(ControllerMock.DEFAULT_ERROR_MESSAGE))

    def set_sensor_temperature(self, sensor_id, temperature):
        self.therm_sensor_api.temperatures[sensor_id] = temperature

    def set_relay_state(self, relay_index, relay_state):
        self.relay_api.relays[relay_index] = relay_state

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

    def __mocked_modify_program(self, program_id, program):
        program_index = -1
        for index in range(len(self.programs)):
            if program_id == self.programs[index].program_id:
                program_index = index
                break
        if program_index < 0:
            raise ProgramError("Program with the given ID not found:{}".format(program.program_id),
                               ProgramError.ERROR_CODE_INVALID_ID)
        existing_program = self.programs[program_index]
        self.programs[program_index] = existing_program.modify_with(program)

    def __mocked_delete_program(self, program_id):
        program_index = -1
        for index in range(len(self.programs)):
            if program_id == self.programs[index].program_id:
                program_index = index
                break
        if program_index < 0:
            raise ProgramError("Program with the given ID not found:{}".format(program_id),
                               ProgramError.ERROR_CODE_INVALID_ID)
        del self.programs[program_index]

    def __mocked_get_programs(self):
        return self.programs

    def __generate_next_program_id(self):
        self.__next_program_id = str(uuid.uuid4())
        self.next_program_id = self.__next_program_id
        return self.__next_program_id

    def __mocked_get_program_state(self, program_id):
        program = self.__get_program_by_id(program_id)
        return program.create_program_state()

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