import time
from app.hardware.therm_sensor_api import ThermSensorApi
from app.logger import Logger
from app.therm_sensor import ThermSensor
from app.hardware.relay_api import RelayApi


class Controller(object):
    RELAYS_COUNT = 8

    def __init__(self, therm_sensor_api=ThermSensorApi(), relay_api=RelayApi()):
        """
        Creates controller instance.
        :param therm_sensor_api: Api to obtain therm sensors and their measurements
        :type therm_sensor_api: ThermSensorApi
        :param relay_api: Api to read and modify relay states
        :type relay_api: RelayApi
        """
        super().__init__()
        self.__sensor_list = None
        self.__programs = []
        self.__therm_sensor_api = therm_sensor_api
        self.__relay_api = relay_api

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

        for existing_program in self.__programs:
            if existing_program.sensor_id == program.sensor_id:
                Logger.error("Program creation rejected - duplicate sensor_id: {}".format(str(program)))
                raise ProgramError("Sensor {} is used in other program".format(program.sensor_id))
            if existing_program.cooling_relay_index == program.cooling_relay_index:
                Logger.error("Program creation rejected - duplicate cooling relay: {}".format(str(program)))
                raise ProgramError("Relay {} is used in other program".format(program.cooling_relay_index))
            if existing_program.heating_relay_index == program.heating_relay_index:
                Logger.error("Program creation rejected - duplicate heating relay: {}".format(str(program)))
                raise ProgramError("Relay {} is used in other program".format(program.heating_relay_index))

        if program.sensor_id not in self.__therm_sensor_api.get_sensor_id_list():
            Logger.error("Program creation rejected - invalid sensor_id: {}".format(str(program)))
            raise ProgramError("Sensor {} is invalid".format(program.sensor_id))

        if program.cooling_relay_index < 0 and program.cooling_relay_index != -1 or \
                program.cooling_relay_index >= Controller.RELAYS_COUNT:
            Logger.error("Program creation rejected - invalid cooling relay index: {}".format(str(program)))
            raise ProgramError("Relay {} is invalid".format(program.cooling_relay_index))

        if program.heating_relay_index < 0 and program.heating_relay_index != -1 or \
                program.heating_relay_index >= Controller.RELAYS_COUNT:
            Logger.error("Program creation rejected - invalid heating relay index: {}".format(str(program)))
            raise ProgramError("Relay {} is invalid".format(program.cooling_relay_index))

        Logger.info("Program created {}".format(str(program)))
        self.__programs.append(program)

    def get_programs(self):
        """
        Returns existing programs list
        :return: List of created programs
        :rtype: list
        """
        return self.__programs


class ProgramError(Exception):
    """Exception class for program errors """
    pass
