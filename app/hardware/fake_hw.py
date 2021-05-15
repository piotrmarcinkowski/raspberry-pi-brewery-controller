from app.logger import Logger
from event_bus import EventBus

bus = EventBus()


class FakeHardware(object):
    FAKE_SENSORS = [
        "fake_sensor_1",
        "fake_sensor_2",
        "fake_sensor_3",
        "fake_sensor_4"
    ]

    def __init__(self, relay_gpio_channels, low_voltage_control=True) -> None:
        super().__init__()
        self.__fake_relay_states = [0] * len(relay_gpio_channels)
        self.__fake_sensors_temperature = {sensor: 18.0 for sensor in FakeHardware.FAKE_SENSORS}

    def get_relay_state(self, relay_index):
        Logger.info("FAKE read relay[{}]={}".format(relay_index, self.__fake_relay_states[relay_index]))
        return self.__fake_relay_states[relay_index]

    def set_relay_state(self, relay_index, state):
        Logger.info("FAKE set relay[{}]={}".format(relay_index, relay_index, state))
        self.__fake_relay_states[relay_index] = state

    def get_sensors(self):
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

