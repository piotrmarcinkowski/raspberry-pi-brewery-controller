import time
import atexit
from app.hardware.therm_sensor_api import ThermSensorApi, NoSensorFoundError, ThermSensorError
from app.logger import Logger
from app.therm_sensor import ThermSensor
from app.hardware.relay_api import RelayApi
from app.storage import Storage
from threading import RLock


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
        self.__sensors = None
        self.__programs = []
        self.__therm_sensor_api = therm_sensor_api
        self.__relay_api = relay_api
        self.__storage = storage
        self.__lock = RLock()

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

        Logger.info("Staring main loop")
        while not main_loop_exit_condition():
            programs = self.get_programs()
            for program in programs:
                program.update()
            try:
                time.sleep(interval_secs)
            except KeyboardInterrupt:
                Logger.info("Keyboard interrupt")
                break

        Logger.info("Controller stopped")

    def __clean_up(self):
        Logger.info("Cleaning up")

        Logger.info("Deactivating all programs")
        programs = self.get_programs()
        for program in programs:
            program.active = False

    def __load_programs(self):
        Logger.info("Loading programs")
        self.__lock.acquire()
        try:
            self.__programs = self.__storage.load_programs()
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
        :raises ProgramError: if there is already a program that uses the same thermal sensor or heating/cooling relay
        """
        Logger.info("Create program:{}".format(str(program)))
        self.__lock.acquire()
        try:
            programs = self.__programs.copy()
            self.__validate_program(program, programs)
            programs.append(program)
            try:
                self.__storage.store_programs(programs)
                Logger.info("Program created {}".format(str(program)))
                self.__programs = programs
            except Exception as e:
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

    def delete_program(self, program_index):
        """
        Deletes specified program, deactivating it first
        """
        Logger.info("Delete program at index:{}".format(program_index))
        self.__lock.acquire()
        try:
            if program_index < 0 or program_index >= len(self.__programs):
                raise ProgramError("Invalid program index: {}".format(program_index))
            programs = self.__programs.copy()
            program = programs.pop(program_index)
            try:
                self.__storage.store_programs(programs)
                program.active = False
                Logger.info("Program deactivated and deleted {}".format(str(program)))
                self.__programs = programs
            except Exception as e:
                Logger.error("Programs store error {}".format(str(e)))
                raise ProgramError(str(e))
        finally:
            self.__lock.release()


class ProgramError(Exception):
    """Exception class for program errors """

    def __init__(self, message=""):
        super().__init__(message)



