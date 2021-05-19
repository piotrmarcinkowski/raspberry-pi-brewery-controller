from app.program import Program, ProgramState
from app.hardware.therm_sensor_api import ThermSensorApi, NoSensorFoundError, ThermSensorError, SensorNotReadyError
from app.logger import Logger
from app.therm_sensor import ThermSensor
from app.hardware.relay_api import RelayApi


class Monitor(object):
    """
    This class is responsible for monitoring single program temperature, reading sensor associated with that program and
    taking actions if current temperature is out of valid range
    """

    def __init__(self, program: Program, therm_sensor_api=None, relay_api=None):
        """
        Creates controller instance.
        :param therm_sensor_api: Api to obtain therm sensors and their measurements
        :type therm_sensor_api: ThermSensorApi
        :param relay_api: Api to read and modify relay states
        :type relay_api: RelayApi
        """
        super().__init__()
        self.__program = program
        self.__therm_sensor_api = therm_sensor_api
        self.__relay_api = relay_api

    def check(self):
        """
        Validates given program temperature. If it's out of allowed range it will trigger actions, either
        turn on cooling or heating. This function should be called repeatedly in short intervals to keep the
        correct temperature of the program
        """
        if not self.__program.active:
            self.__ensure_relays_are_disabled()
            return

        try:
            current_temperature = self.__therm_sensor_api.get_sensor_temperature(self.__program.sensor_id)
        except SensorNotReadyError as e:
            Logger.error("Program check skipped - sensor not ready - program: {}".format(str(self)))
            self.__set_error(e)
            self.__ensure_relays_are_disabled()
            return
        except NoSensorFoundError as e:
            Logger.error("Program check error - no sensor found - program: {}".format(str(self)))
            self.__set_error(e)
            self.__ensure_relays_are_disabled()
            return

        self.__set_error(None)

        program_min_temp = self.__program.min_temperature
        program_max_temp = self.__program.max_temperature
        program_middle_temp = (program_max_temp + program_min_temp) / 2

        cooling_available = self.__cooling_available()
        if cooling_available:
            cooling_active = self.__is_cooling()
            cooling_necessary = cooling_active
            if cooling_active:
                cooling_necessary = current_temperature > program_middle_temp
            else:
                cooling_necessary = current_temperature > program_max_temp
            self.__set_cooling(cooling_necessary)

        heating_available = self.__heating_available()
        if heating_available:
            heating_active = self.__is_heating()
            heating_necessary = heating_active
            if heating_active:
                heating_necessary = current_temperature < program_middle_temp
            else:
                heating_necessary = current_temperature < program_min_temp
            self.__set_heating(heating_necessary)

    def __ensure_relays_are_disabled(self):
        if self.__cooling_available() and self.__is_cooling():
            self.__set_cooling(False)
        if self.__heating_available() and self.__is_heating():
            self.__set_heating(False)

    def __set_error(self, error):
        self.error = error

    def get_error(self):
        return self.error

    def __cooling_available(self):
        return self.__program.cooling_relay_index != -1

    def __is_cooling(self):
        return self.__relay_api.get_relay_state(self.__program.cooling_relay_index)

    def __set_cooling(self, cooling):
        cooling_relay_index = self.__program.cooling_relay_index
        if cooling_relay_index == -1:
            return
        relay_state = 1 if cooling else 0
        if self.__relay_api.get_relay_state(cooling_relay_index) != relay_state:
            Logger.info("{} cooling relay:{} {}".format(
                "Activating" if relay_state == 1 else "Deactivating",
                cooling_relay_index, self.__program))
            self.__relay_api.set_relay_state(cooling_relay_index, relay_state)

    def __heating_available(self):
        return self.__program.heating_relay_index != -1

    def __is_heating(self):
        return self.__relay_api.get_relay_state(self.__program.heating_relay_index)

    def __set_heating(self, heating):
        heating_relay_index = self.__program.heating_relay_index
        if heating_relay_index == -1:
            return
        relay_state = 1 if heating else 0
        if self.__relay_api.get_relay_state(heating_relay_index) != relay_state:
            Logger.info("{} heating relay:{} {}".format(
                "Activating" if relay_state == 1 else "Deactivating",
                heating_relay_index, self.__program))
            self.__relay_api.set_relay_state(heating_relay_index, relay_state)
