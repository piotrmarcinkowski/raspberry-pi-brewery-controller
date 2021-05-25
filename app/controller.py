import time
import atexit
import uuid
from app.program import Program, ProgramState
from app.hardware.therm_sensor_api import ThermSensorApi, NoSensorFoundError, ThermSensorError, SensorNotReadyError
from app.logger import Logger
from app.therm_sensor import ThermSensor
from app.hardware.relay_api import RelayApi
from app.storage import Storage
from threading import RLock
from monitor import Monitor
from utils import EventBus

_bus = EventBus()


class Controller(object):
    RELAYS_COUNT = len(RelayApi.RELAY_GPIO_CHANNELS)

    def __init__(self, therm_sensor_api=None, relay_api=None, storage=None):
        """
        Creates controller instance.
        :param therm_sensor_api: Api to obtain therm sensors and their measurements
        :type therm_sensor_api: ThermSensorApi
        :param relay_api: Api to read and modify relay states
        :type relay_api: RelayApi
        :param storage: Api for storing data
        :type storage: Storage
        """
        super().__init__()
        self.__sensors = None
        self.__programs = []
        self.__monitors = []
        self.__therm_sensor_api = therm_sensor_api
        self.__relay_api = relay_api
        self.__storage = storage if storage is not None else Storage()
        self.__lock = RLock()

    def __set_programs(self, programs):
        self.__programs = programs
        self.__monitors = [Monitor(program, self.__therm_sensor_api, self.__relay_api) for program in programs]
        _bus.emit('programs_updated', programs)

    def __default_main_loop_exit_condition(self):
        # Never exit main loop by default, keep the program running, this is needed to alter the behavior in tests only
        return False

    def run(self, interval_secs=1.0, main_loop_exit_condition=None):
        """
        Start controller. After this function is called the controller will periodically update active programs to
        maintain requested temperature by turning on/off coolers/heaters attached to relays
        """
        Logger.info("Starting controller")

        atexit.register(self.__clean_up)
        self.__load_programs()

        if main_loop_exit_condition is None:
            main_loop_exit_condition = self.__default_main_loop_exit_condition

        Logger.info("Starting main loop")

        while not main_loop_exit_condition():

            self.__lock.acquire()
            try:
                programs = self.__programs
                monitors = self.__monitors
            finally:
                self.__lock.release()

            self.__deactivate_all_unassigned_relays(programs)

            for monitor in monitors:
                monitor.check()
            try:
                time.sleep(interval_secs)
            except KeyboardInterrupt:
                Logger.info("Keyboard interrupt")
                break

        Logger.info("Controller stopped")

    def __clean_up(self):
        Logger.info("Deactivating all programs")
        # remove all programs
        self.__set_programs([])
        # deactivate all relays that are not assigned to any program
        self.__deactivate_all_unassigned_relays()

    def __deactivate_all_unassigned_relays(self, programs=[]):
        for relay_index in range(Controller.RELAYS_COUNT):
            if not Controller.__is_relay_assigned(relay_index, programs) and \
                    self.__relay_api.get_relay_state(relay_index):
                self.__relay_api.set_relay_state(relay_index, 0)

    @staticmethod
    def __is_relay_assigned(relay_index, programs):
        for program in programs:
            if program.cooling_relay_index == relay_index or program.heating_relay_index == relay_index:
                return True
        return False

    def __load_programs(self):
        Logger.info("Loading programs")
        self.__lock.acquire()
        try:
            programs = self.__storage.load_programs()
            for program in programs:
                if not program.program_id:
                    raise ProgramError("Stored program has no id: {}".format(program))
            self.__set_programs(programs)
        finally:
            self.__lock.release()
        Logger.info("Programs loaded {}".format(self.__programs))

    def get_therm_sensors(self):
        """
        Returns available therm sensors of ThermSensor type
        :return: List of available therm sensors
        :rtype: list
        """

        self.__lock.acquire()
        try:
            if self.__sensors is None:
                sensors = []
                stored_sensors = {sensor.id: sensor for sensor in self.__storage.load_sensors()}
                existing_sensor_ids = self.__therm_sensor_api.get_sensor_id_list()
                for existing_sensor_id in existing_sensor_ids:
                    if existing_sensor_id in stored_sensors:
                        sensors.append(stored_sensors[existing_sensor_id])
                    else:
                        sensors.append(ThermSensor(existing_sensor_id))
                self.__sensors = sensors

            return self.__sensors
        finally:
            self.__lock.release()

    def get_therm_sensor_temperature(self, sensor_id):
        """
        Returns current temperature of therm sensor with a given sensor_id
        :param sensor_id: Id of the sensor to read temperature from
        :type sensor_id: str
        :return: Temperature read from the sensor
        :rtype float
        :raises NoSensorFoundError: if the sensor with the given id could not be found
        :raises SensorNotReadyError: if the sensor is not ready yet
        """

        return self.__therm_sensor_api.get_sensor_temperature(sensor_id)

    def set_therm_sensor_name(self, sensor_id, name):
        """
        Sets a name for given therm sensor making it easier to distinguish
        :param sensor_id: therm sensor id
        :param name: name to assign to the sensor
        :return: Returns sensor object with name set
        :rtype: ThermSensor
        :raises NoSensorFoundError: when a sensor with given sensor_id was not found
        :raises ThermSensorError: when there was other problem with setting sensor name
        """
        Logger.info("Set sensor name {}->{}".format(sensor_id, name))
        self.__lock.acquire()
        try:
            sensors = self.get_therm_sensors().copy()
            modified_sensor = None
            for index in range(len(sensors)):
                if sensors[index].id == sensor_id:
                    modified_sensor = ThermSensor(sensor_id, name)
                    sensors[index] = modified_sensor

            if modified_sensor is None:
                raise NoSensorFoundError(sensor_id)

            try:
                self.__storage.store_sensors(sensors)
                Logger.info("Sensors stored {}".format(str(sensors)))
                self.__sensors = sensors
                return modified_sensor
            except Exception as e:
                Logger.error("Sensors store error {}".format(str(e)))
                raise ThermSensorError()
        finally:
            self.__lock.release()

    def get_relays_state(self):
        """
        Return list with available relays' states. Values in the list are integers 0 or 1
        :return: List with the states of each available relay
        :rtype: list
        """

        return [self.__relay_api.get_relay_state(relay_index) for relay_index in range(self.RELAYS_COUNT)]

    def create_program(self, program):
        """
        Creates a new program that will monitor temperature at specified therm sensor and control it by activating
        cooling/heating
        :param program: Program to create
        :return program: Program that is a copy of the program given as parameter with unique generated ID.
        :raises ProgramError: if there is already a program that uses the same thermal sensor or heating/cooling relay
        """
        Logger.info("Create program:{}".format(str(program)))
        self.__lock.acquire()
        try:
            program_generated_id = str(uuid.uuid4())
            created_program = Program(program_generated_id, program.program_name,
                                      program.sensor_id, program.heating_relay_index, program.cooling_relay_index,
                                      program.min_temperature, program.max_temperature, program.active)
            programs = self.__programs.copy()
            self.__validate_program(created_program, programs)
            programs.append(created_program)
            try:
                self.__storage.store_programs(programs)
                Logger.info("Program created {}".format(str(created_program)))
                self.__set_programs(programs)
            except Exception as e:
                Logger.error("Programs store error {}".format(str(e)))
                raise ProgramError(str(e))
            return created_program
        finally:
            self.__lock.release()

    @staticmethod
    def find_program_index(program_id, programs):
        for index in range(len(programs)):
            if program_id == programs[index].program_id:
                return index
        return -1

    def modify_program(self, program_id, program):
        """
        Modifies existing program
        :param program_id: Id of the program to modify
        :param program: Modified program. The existing program will be replaced by this one. Note that the program
        Id is provided separately, it's not being being taken from the program itself, it can be empty there in fact
        :raises ProgramError: if there is already a program that uses the same thermal sensor or heating/cooling relay
            or the program was not found and has to be created first
        """
        Logger.info("Modify program {}".format(str(program)))
        self.__lock.acquire()
        try:
            updated_programs = self.__programs.copy()
            program_index = self.find_program_index(program_id, updated_programs)
            if program_index < 0:
                raise ProgramError("Program with the given ID not found:{}".format(program.program_id),
                                   ProgramError.ERROR_CODE_INVALID_ID)
            existing_program = updated_programs[program_index]
            updated_programs[program_index] = existing_program.modify_with(program)
            self.__validate_program(program, updated_programs, skip_index=program_index)
            try:
                self.__storage.store_programs(updated_programs)
                self.__set_programs(updated_programs)
                Logger.info("Program modified {} -> {}".format(str(existing_program), str(program)))
                return updated_programs[program_index]
            except Exception as e:
                Logger.error("Programs store error {}".format(str(e)))
                raise ProgramError(str(e))
        finally:
            self.__lock.release()

    def __validate_program(self, program, existing_programs, skip_index=-1):
        for index in range(len(existing_programs)):
            if index == skip_index:
                continue
            existing_program = existing_programs[index]
            if existing_program.sensor_id == program.sensor_id:
                Logger.error("Program rejected - duplicate sensor_id: {}".format(str(program)))
                raise ProgramError("Sensor {} is used in other program".format(program.sensor_id))
            if program.cooling_relay_index != -1 and existing_program.cooling_relay_index == program.cooling_relay_index:
                Logger.error("Program rejected - duplicate cooling relay: {}".format(str(program)))
                raise ProgramError("Relay {} is used in other program".format(program.cooling_relay_index))
            if program.heating_relay_index != -1 and existing_program.heating_relay_index == program.heating_relay_index:
                Logger.error("Program rejected - duplicate heating relay: {}".format(str(program)))
                raise ProgramError("Relay {} is used in other program".format(program.heating_relay_index))
        if program.sensor_id not in self.__therm_sensor_api.get_sensor_id_list():
            Logger.error("Program rejected - invalid sensor_id: {}".format(str(program)))
            raise ProgramError("Sensor {} is invalid".format(program.sensor_id))
        if program.cooling_relay_index < 0 and program.cooling_relay_index != -1 or \
                program.cooling_relay_index >= Controller.RELAYS_COUNT:
            Logger.error("Program rejected - invalid cooling relay index: {}".format(str(program)))
            raise ProgramError("Relay {} is invalid".format(program.cooling_relay_index))
        if program.heating_relay_index < 0 and program.heating_relay_index != -1 or \
                program.heating_relay_index >= Controller.RELAYS_COUNT:
            Logger.error("Program rejected - invalid heating relay index: {}".format(str(program)))
            raise ProgramError("Relay {} is invalid".format(program.cooling_relay_index))

    def get_programs(self):
        """
        Returns existing programs list
        :return: List of created programs
        :rtype: list
        """
        self.__lock.acquire()
        try:
            return self.__programs
        finally:
            self.__lock.release()

    def delete_program(self, program_id):
        """
        Deletes specified program, deactivating it first
        """
        Logger.info("Delete program:{}".format(program_id))
        self.__lock.acquire()
        try:
            programs = self.__programs.copy()
            program_index = self.find_program_index(program_id, programs)
            if program_index < 0:
                raise ProgramError("Program with the given ID not found:{}".format(program_id),
                                   ProgramError.ERROR_CODE_INVALID_ID)
            program = programs.pop(program_index)
            try:
                self.__storage.store_programs(programs)
                Logger.info("Program deleted {}".format(str(program)))
                self.__set_programs(programs)
            except Exception as e:
                Logger.error("Programs store error {}".format(str(e)))
                raise ProgramError(str(e))
        finally:
            self.__lock.release()

    def get_program_state(self, program_id):
        """
        Returns current state of the given program
        :return: State of the program
        :rtype: ProgramState
        """
        self.__lock.acquire()
        try:
            program_index = self.find_program_index(program_id, self.__programs)
            if program_index < 0:
                raise ProgramError("Program with the given ID not found:{}".format(program_id),
                                   ProgramError.ERROR_CODE_INVALID_ID)
            return self.__programs[program_index].create_program_state(self.__therm_sensor_api, self.__relay_api)
        finally:
            self.__lock.release()

    def get_program_states(self):
        """
        Returns states of all programs as an array
        :return: States of existing programs
        :rtype: list
        """
        self.__lock.acquire()
        try:
            return [self.__programs[program_index].create_program_state(self.__therm_sensor_api, self.__relay_api) for
                    program_index in range(len(self.__programs))]
        finally:
            self.__lock.release()


class ProgramError(Exception):
    """Exception class for program errors """

    ERROR_CODE_INVALID_ID = "invalid_id"
    ERROR_CODE_INVALID_OPERATION = "invalid_operation"

    def __init__(self, message="", error_code=ERROR_CODE_INVALID_OPERATION):
        super().__init__(message)
        self.error_code = error_code

    def get_error_code(self):
        return self.error_code
