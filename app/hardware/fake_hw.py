from app.logger import Logger
from event_bus import EventBus
from app.hardware.relay_api import RelayApi
from program import Program
from storage import Storage

bus = EventBus()


class FakeHardware(object):
    FAKE_SENSORS = [
        "fake_sensor_1",
        "fake_sensor_2",
        "fake_sensor_3",
        "fake_sensor_4"
    ]

    def __init__(self, relay_gpio_channels=RelayApi.RELAY_GPIO_CHANNELS, low_voltage_control=True) -> None:
        super().__init__()
        self.__fake_relay_states = [0] * len(relay_gpio_channels)
        self.__fake_sensors_temperature = {sensor: 18.0 for sensor in FakeHardware.FAKE_SENSORS}

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
        Logger.info("FAKE set relay[{}]={}".format(relay_index, relay_index, state))
        self.__fake_relay_states[relay_index] = state

    def get_sensor_id_list(self):
        return FakeHardware.FAKE_SENSORS

    def get_sensor_temperature(self, sensor_id):
        self.__update_temperatures()
        return self.__fake_sensors_temperature[sensor_id]

    @bus.on('programs_updated')
    def programs_updated(self, programs):
        Logger.info("FAKE programs updated")
        pass

    def __update_temperatures(self):
        pass

