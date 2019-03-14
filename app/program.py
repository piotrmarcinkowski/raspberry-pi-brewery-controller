from app.hardware.therm_sensor_api import ThermSensorApi
from app.hardware.relay_api import RelayApi
import json


class Program(object):
    """
    Represents a single program that defines thermal sensor and up to two relays that enable cooling or heating
    in order to keep temperature at defined level
    """

    def __init__(self, sensor_id,
                 heating_relay_index, cooling_relay_index,
                 min_temperature, max_temperature,
                 therm_sensor_api=ThermSensorApi(), relay_api=RelayApi(),
                 active=True):
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
        :param active: Sets the program to activated or deactivated. Deactivated program skips any actions
        :type active: bool
        """
        super().__init__()
        self.__sensor_id = sensor_id
        self.__heating_relay_index = heating_relay_index
        self.__cooling_relay_index = cooling_relay_index
        self.__min_temperature = min_temperature
        self.__max_temperature = max_temperature
        self.__relay_api = relay_api
        self.__therm_sensor_api = therm_sensor_api
        self.__active = active

    def update(self):
        """
        Reads temperature from thermal sensor and takes actions (enable cooling_active, heating_active) if it's beyond allowed range
        """
        if not self.active:
            return

        current_temperature = self.__therm_sensor_api.get_sensor_temperature(self.__sensor_id)
        cooling_active = current_temperature > self.__max_temperature
        heating_active = current_temperature < self.__min_temperature

        self.__set_cooling(cooling_active)
        self.__set_heating(heating_active)

    @property
    def active(self):
        return self.__active

    @active.setter
    def active(self, active):
        """
        Activates or deactivates a program. Activated program will call update automatically. Deactivated program
        will also deactivate all controlled relays
        :param active: True to activate the program, False otherwise
        """
        if self.__active is active:
            return
        self.__active = active
        if active:
            self.update()
        else:
            self.__set_cooling(False)
            self.__set_heating(False)

    @property
    def sensor_id(self):
        return self.__sensor_id

    @property
    def heating_relay_index(self):
        return self.__heating_relay_index

    @property
    def cooling_relay_index(self):
        return self.__cooling_relay_index

    @property
    def min_temperature(self):
        return self.__min_temperature

    @property
    def max_temperature(self):
        return self.__max_temperature

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

    def to_json_data(self):
        return {"sensor_id": self.__sensor_id,
                "heating_relay_index": self.__heating_relay_index,
                "cooling_relay_index": self.__cooling_relay_index,
                "min_temp": self.__min_temperature,
                "max_temp": self.__max_temperature,
                "active": self.active
                }

    def to_json(self):
        data = self.to_json_data()
        return json.dumps(data)

    @classmethod
    def from_json_data(cls, data):
        return Program(data["sensor_id"],
                       data["heating_relay_index"],
                       data["cooling_relay_index"],
                       data["min_temp"],
                       data["max_temp"],
                       active=data["active"])

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls.from_json_data(data)

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__sensor_id == other.__sensor_id and \
                   self.__cooling_relay_index == other.__cooling_relay_index and \
                   self.__heating_relay_index == other.__heating_relay_index and \
                   self.__min_temperature == other.__min_temperature and \
                   self.__max_temperature == other.__max_temperature and \
                   self.__active == other.__active

        return False

    def __str__(self):
        return "Program [sensor_id:{} heating_relay_index:{} cooling_relay_index:{} min_temp:{} max_temp:{} active:{}]".format(
            self.sensor_id, self.heating_relay_index, self.cooling_relay_index, self.min_temperature,
            self.max_temperature, self.active)
