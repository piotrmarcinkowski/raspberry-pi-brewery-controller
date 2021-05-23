import json


class Program(object):
    """
    Represents a single program that defines thermal sensor and up to two relays that enable cooling or heating
    in order to keep temperature at defined level
    """

    UNDEFINED_ID = ""
    UNDEFINED_SENSOR_ID = ""
    UNDEFINED_NAME = ""
    UNDEFINED_HEATING_RELAY_INDEX = -1
    UNDEFINED_COOLING_RELAY_INDEX = -1
    UNDEFINED_MIN_TEMP = 0.0
    UNDEFINED_MAX_TEMP = 0.0
    UNDEFINED_ACTIVE = False

    def __init__(self,
                 program_id=UNDEFINED_ID,
                 program_name=UNDEFINED_NAME,
                 sensor_id=UNDEFINED_SENSOR_ID,
                 heating_relay_index=UNDEFINED_HEATING_RELAY_INDEX,
                 cooling_relay_index=UNDEFINED_COOLING_RELAY_INDEX,
                 min_temperature=UNDEFINED_MIN_TEMP,
                 max_temperature=UNDEFINED_MAX_TEMP,
                 active=UNDEFINED_ACTIVE):
        """
        Creates program instance.
        :param program_id: Id of the program in UUID format
        :type program_id: str
        :param program_name: Name of the program
        :type program_name: str
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
        :param active: Sets the program to activated or deactivated. Deactivated program skips any actions
        :type active: bool
        """
        super().__init__()
        self.__program_id = program_id
        self.__program_name = program_name
        self.__sensor_id = sensor_id
        self.__heating_relay_index = heating_relay_index
        self.__cooling_relay_index = cooling_relay_index
        self.__min_temperature = min_temperature
        self.__max_temperature = max_temperature
        self.__active = active


    @property
    def active(self):
        return self.__active

    @property
    def program_id(self):
        return self.__program_id

    @property
    def program_name(self):
        return self.__program_name

    @property
    def program_crc(self):
        return str(hash((self.program_id, self.program_name, self.sensor_id,
                    self.cooling_relay_index, self.heating_relay_index,
                    self.min_temperature, self.max_temperature, self.active)))

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

    def create_program_state(self, therm_sensor_api, relay_api):
        heating_activated = False
        if self.heating_relay_index != Program.UNDEFINED_HEATING_RELAY_INDEX:
            heating_activated = relay_api.get_relay_state(self.heating_relay_index)
        cooling_activated = False
        if self.cooling_relay_index != Program.UNDEFINED_HEATING_RELAY_INDEX:
            cooling_activated = relay_api.get_relay_state(self.cooling_relay_index)
        return ProgramState(self.program_id,
                            therm_sensor_api.get_sensor_temperature(self.sensor_id),
                            self.program_crc,
                            heating_activated, cooling_activated)

    def modify_with(self, program, program_name=None, sensor_id=None,
                    heating_relay_index=None, cooling_relay_index=None,
                    min_temperature=None, max_temperature=None, active=None):
        return Program(
            program_id=self.program_id,
            program_name=program.program_name if program_name is None else program_name,
            sensor_id=program.sensor_id if sensor_id is None else sensor_id,
            heating_relay_index=program.heating_relay_index if heating_relay_index is None else heating_relay_index,
            cooling_relay_index=program.cooling_relay_index if cooling_relay_index is None else cooling_relay_index,
            min_temperature=program.min_temperature if min_temperature is None else min_temperature,
            max_temperature=program.max_temperature if max_temperature is None else max_temperature,
            active=program.active if active is None else active
        )

    def to_json_data(self):
        return {"id": self.program_id,
                "name": self.program_name,
                "crc": self.program_crc,
                "sensor_id": self.sensor_id,
                "heating_relay_index": self.heating_relay_index,
                "cooling_relay_index": self.cooling_relay_index,
                "min_temp": self.min_temperature,
                "max_temp": self.max_temperature,
                "active": self.active
                }

    def to_json(self):
        data = self.to_json_data()
        return json.dumps(data)

    @classmethod
    def from_json_data(cls, data):
        return Program(program_id=data.get("id", Program.UNDEFINED_ID),
                       program_name=data.get("name", Program.UNDEFINED_NAME),
                       sensor_id=data.get("sensor_id", Program.UNDEFINED_SENSOR_ID),
                       heating_relay_index=data.get("heating_relay_index", Program.UNDEFINED_HEATING_RELAY_INDEX),
                       cooling_relay_index=data.get("cooling_relay_index", Program.UNDEFINED_COOLING_RELAY_INDEX),
                       min_temperature=data.get("min_temp", Program.UNDEFINED_MIN_TEMP),
                       max_temperature=data.get("max_temp", Program.UNDEFINED_MAX_TEMP),
                       active=data.get("active", Program.UNDEFINED_ACTIVE))

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls.from_json_data(data)

    def __eq__(self, other):
        if type(other) is type(self):
            return self.program_crc == other.program_crc

        return False

    def __str__(self):
        return "Program [program_id:{} program_name:{} program_crc:{} " \
               "sensor_id:{} heating_relay_index:{} cooling_relay_index:{} min_temp:{} " \
               "max_temp:{} active:{}]".format(
                self.program_id, self.program_name, self.program_crc,
                self.sensor_id, self.heating_relay_index, self.cooling_relay_index, self.min_temperature,
                self.max_temperature, self.active)

    def __repr__(self):
        return self.__str__()


class ProgramState:
    def __init__(self,
                 program_id,
                 current_temperature,
                 program_crc,
                 heating_activated=False,
                 cooling_activated=False):
        """
        Creates program state instance.
        :param program_id: Id of the program in UUID format that state refers to
        :type program_id: str
        :param current_temperature: Current temperature reported from the thermal sensor associated with the program
        :type current_temperature: float
        :param program_crc: Crc of the program this state refers to
        :type program_crc: str
        :param heating_activated: True if heating for the program is active now
        :type heating_activated: bool
        :param cooling_activated: True if cooling for the program is active now
        :type cooling_activated: bool
        """
        super().__init__()
        self.__program_id = program_id
        self.__current_temperature = current_temperature
        self.__program_crc = program_crc
        self.__heating_activated = heating_activated
        self.__cooling_activated = cooling_activated

    @property
    def program_id(self):
        return self.__program_id

    @property
    def current_temperature(self):
        return self.__current_temperature

    @property
    def program_crc(self):
        return self.__program_crc

    @property
    def heating_activated(self):
        return self.__heating_activated

    @property
    def cooling_activated(self):
        return self.__cooling_activated

    def to_json_data(self):
        return {"id": self.program_id,
                "currentTemp": self.current_temperature,
                "crc": self.program_crc,
                "heatingActivated": self.heating_activated,
                "coolingActivated": self.cooling_activated}

    def to_json(self):
        data = self.to_json_data()
        return json.dumps(data)
