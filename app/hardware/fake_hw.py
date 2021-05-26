from app.logger import Logger
from utils import EventBus
from app.hardware.relay_api import RelayApi
from program import Program
from storage import Storage
from datetime import datetime

_bus = EventBus()
_programs = []
ENV_TEMPERATURE = 30.0
SIMULATION_SPEED = 2  # temperature delta is 2 degrees per minute

@_bus.on('programs_updated')
def programs_updated(programs):
    Logger.info("FAKE programs updated")
    global _programs
    _programs = programs


class FakeHardware(object):
    FAKE_SENSORS = [
        "fake_sensor_1",
        "fake_sensor_2",
        "fake_sensor_3",
        "fake_sensor_4"
    ]

    def __init__(self, relay_gpio_channels=RelayApi.RELAY_GPIO_CHANNELS, low_voltage_control=True) -> None:
        super().__init__()
        Logger.info("FAKE init fake hardware")
        self.__fake_relay_states = [0] * len(relay_gpio_channels)
        self.__fake_sensors_temperature = {sensor: 18.0 for sensor in FakeHardware.FAKE_SENSORS}
        global ENV_TEMPERATURE
        self.__env_temperature = ENV_TEMPERATURE
        self.__last_temp_update_timestamp = 0
        global SIMULATION_SPEED
        self.__temp_factor = SIMULATION_SPEED / 60

    @property
    def therm_sensor_api(self):
        return self

    @property
    def relay_api(self):
        return self

    @property
    def storage(self):
        storage = Storage(programs_file_name="fake_programs", sensors_file_name="fake_sensors")
        existing_fake_programs = storage.load_programs()
        if len(existing_fake_programs) == 0:
            Logger.info("FAKE creating initial fake programs")
            storage.store_programs([Program(program_id="fake_id_1", sensor_id=FakeHardware.FAKE_SENSORS[1], program_name="Fake Program 1",
                                            cooling_relay_index=1, min_temperature=18.0, max_temperature=19.0,
                                            active=True)])
        return storage

    def get_relay_state(self, relay_index):
        return self.__fake_relay_states[relay_index]

    def set_relay_state(self, relay_index, state):
        Logger.info("FAKE set relay[{}]={}".format(relay_index, state))
        self.__fake_relay_states[relay_index] = state

    def get_sensor_id_list(self):
        return FakeHardware.FAKE_SENSORS

    def get_sensor_temperature(self, sensor_id):
        self.__maybe_update_fake_temperatures()
        return self.__fake_sensors_temperature[sensor_id]

    def __update_fake_temperatures(self):
        now = datetime.timestamp(datetime.now())
        if self.__last_temp_update_timestamp == 0:
            self.__last_temp_update_timestamp = now
        time_delta = now - self.__last_temp_update_timestamp
        temp_delta = self.__temp_factor * time_delta
        self.__last_temp_update_timestamp = now

        for program in _programs:
            sensor_id = program.sensor_id
            current_temp = self.__fake_sensors_temperature[sensor_id]
            temp_delta_sign = 1 if self.__env_temperature - current_temp > 0 else -1
            if self.__is_cooling_active(program):
                temp_delta_sign = -1
            if self.__is_heating_active(program):
                temp_delta_sign = 1
            new_temp = current_temp + temp_delta_sign * temp_delta
            self.__fake_sensors_temperature[sensor_id] = new_temp

    def __is_cooling_active(self, program):
        if program.cooling_relay_index != -1:
            return self.__fake_relay_states[program.cooling_relay_index] == 1
        return False

    def __is_heating_active(self, program):
        if program.heating_relay_index != -1:
            return self.__fake_relay_states[program.heating_relay_index] == 1
        return False

    def __maybe_update_fake_temperatures(self):
        now = datetime.timestamp(datetime.now())
        if self.__last_temp_update_timestamp == 0:
            self.__last_temp_update_timestamp = now

        if now - self.__last_temp_update_timestamp > 1:
            self.__update_fake_temperatures()
