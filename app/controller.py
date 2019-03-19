import time
from app.hardware.therm_sensor_api import ThermSensorApi
from app.logger import Logger
from app.therm_sensor import ThermSensor
from app.hardware.relay_api import RelayApi
from app.storage import Storage
from threading import Lock


class Controller(object):
    RELAYS_COUNT = 8

    def __init__(self, therm_sensor_api=ThermSensorApi(), relay_api=RelayApi(), storage=Storage()):
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
        self.__sensor_list = None
        self.__programs = []
        self.__therm_sensor_api = therm_sensor_api
        self.__relay_api = relay_api
        self.__storage = storage
        self.__lock = Lock()

    def run(self):
        """
        Start controller. After this function is called the controller will periodically update active programs to
        maintain requested temperature by turning on/off coolers attached to relays
        """
        Logger.info("Starting controller")
        while True:
            time.sleep(1)
            pass
        Logger.info("Controller stopped")

    def get_therm_sensors(self):
        """
        Returns available therm sensors of ThermSensor type
        :return: List of available therm sensors
        :rtype: list
        """

        if self.__sensor_list is None:
            sensor_ids = self.__therm_sensor_api.get_sensor_id_list()
            self.__sensor_list = [ThermSensor(sensor_id) for sensor_id in sensor_ids]

        return self.__sensor_list

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
        :raises ProgramError: if there is already a program that uses the same thermal sensor or heating/cooling relay
        """
        Logger.info("Create program:{}".format(str(program)))
        self.__lock.acquire()
        try:
            self.__validate_program(program, self.__programs)
            self.__programs.append(program)
            try:
                self.__storage.store_programs(self.__programs)
                Logger.info("Program created {}".format(str(program)))
            except Exception as e:
                # restore programs before adding the new one
                self.__programs.remove(program)
                Logger.error("Programs store error {}".format(str(e)))
                raise ProgramError(str(e))
        finally:
            self.__lock.release()

    def modify_program(self, program_index, program):
        """
        Modifies existing program
        :param program_index: Program index to replace
        :param program: Modified program
        :raises ProgramError: if there is already a program that uses the same thermal sensor or heating/cooling relay
                """
        Logger.info("Modify program at index:{} with {}".format(program_index, str(program)))
        self.__lock.acquire()
        try:
            if program_index < 0 or program_index >= len(self.__programs):
                raise ProgramError("Program with index:{} does not exist".format(program_index))
            programs = self.__programs.copy()
            replaced_program = programs[program_index]
            programs[program_index] = program
            self.__validate_program(program, programs, skip_index=program_index)
            try:
                self.__storage.store_programs(programs)
                self.__programs = programs
                Logger.info("Program modified {} -> {}".format(str(replaced_program), str(program)))
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
            if existing_program.cooling_relay_index == program.cooling_relay_index:
                Logger.error("Program rejected - duplicate cooling relay: {}".format(str(program)))
                raise ProgramError("Relay {} is used in other program".format(program.cooling_relay_index))
            if existing_program.heating_relay_index == program.heating_relay_index:
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

    def delete_program(self, program_index):
        """
        Deletes specified program, deactivating it first
        """
        Logger.info("Delete program at index:{}".format(program_index))
        self.__lock.acquire()
        try:
            if program_index < 0 or program_index >= len(self.__programs):
                raise ProgramError("Invalid program index: {}".format(program_index))
            program = self.__programs.pop(program_index)
            try:
                self.__storage.store_programs(self.__programs)
                program.active = False
                Logger.info("Program deactivated and deleted {}".format(str(program)))
            except Exception as e:
                # restore deleted program, updated programs list could not be stored
                self.__programs.insert(program_index, program)
                Logger.error("Programs store error {}".format(str(e)))
                raise ProgramError(str(e))
        finally:
            self.__lock.release()


class ProgramError(Exception):
    """Exception class for program errors """
    pass
