from app.hardware.therm_sensor_api import ThermSensorApi
from app.hardware.relay_api import RelayApi


class Program(object):
    """
    Represents a single program that defines thermal sensor and up to two relays that enable cooling or heating
    in order to keep temperature at defined level
    """

    def __init__(self, sensor_id,
                 heating_relay_index, cooling_relay_index,
                 min_temperature, max_temperature,
                 therm_sensor_api=ThermSensorApi(), relay_api=RelayApi()):
        """
        Creates program instance.
        :param sensor_id: Id of the thermal sensor to read temperature from
        :type sensor_id: str
        :param heating_relay_index: Index of heating relay (-1 if not used)
        :type heating_relay_index: int
        :param cooling_relay_index: Index of cooling relay (-1 if not used)
        :type cooling_relay_index: int
        :param min_temperature: Minimal allowed temperature. Heating will be activated if exceeded
        :type min_temperature: float
        :param max_temperature: Maximum allowed temperature. Cooling will be activated if exceeded
        :type max_temperature: float
        :param therm_sensor_api: Api to obtain therm sensors and their measurements
        :type therm_sensor_api: ThermSensorApi
        :param relay_api: Api to read and modify relay states
        :type relay_api: RelayApi
        """
        super().__init__()
        self.__sensor_id = sensor_id
        self.__heating_relay_index = heating_relay_index
        self.__cooling_relay_index = cooling_relay_index
        self.__min_temperature = min_temperature
        self.__max_temperature = max_temperature
        self.__relay_api = relay_api
        self.__therm_sensor_api = therm_sensor_api

    def check(self):
        """
        Reads temperature from thermal sensor and takes actions if it's beyond allowed range
        """
        current_temperature = self.__therm_sensor_api.get_sensor_temperature(self.__sensor_id)
        if current_temperature > self.__max_temperature:
            self.__set_cooling(True)
            self.__set_heating(False)

        if current_temperature < self.__min_temperature:
            self.__set_cooling(False)
            self.__set_heating(True)

    def __set_cooling(self, cooling):
        if self.__cooling_relay_index == -1:
            return
        relay_state = 1 if cooling else 0
        if self.__relay_api.get_relay_state(self.__cooling_relay_index) != relay_state:
            self.__relay_api.set_relay_state(self.__cooling_relay_index, relay_state)

    def __set_heating(self, heating):
        if self.__heating_relay_index == -1:
            return
        relay_state = 1 if heating else 0
        if self.__relay_api.get_relay_state(self.__heating_relay_index) != relay_state:
            self.__relay_api.set_relay_state(self.__heating_relay_index, relay_state)
