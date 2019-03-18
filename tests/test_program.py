import unittest
import json
from unittest.mock import Mock
from app.program import Program
from app.hardware.therm_sensor_api import SensorNotReadyError, NoSensorFoundError

SENSOR_ID = "sensor_id"
HEATING_RELAY_INDEX = 1
COOLING_RELAY_INDEX = 2


class ThermSensorApiMock(Mock):

    def __init__(self):
        super().__init__()
        self.get_sensor_temperature = Mock(side_effect=self.__mocked_get_sensor_temperature)
        self.__temperatures = {}

    def set_temperature(self, sensor_id, temperature):
        self.__temperatures[sensor_id] = temperature

    def unset_temperature(self, sensor_id):
        del self.__temperatures[sensor_id]

    def __mocked_get_sensor_temperature(self, sensor_id):
        if sensor_id not in self.__temperatures:
            raise NoSensorFoundError(sensor_id)
        if self.__temperatures[sensor_id] is None:
            raise SensorNotReadyError(sensor_id)
        return self.__temperatures[sensor_id]


class RelayApiMock(Mock):
    RELAYS_COUNT = 8

    def __init__(self):
        super().__init__()
        self.get_relay_state = Mock(side_effect=self.__mocked_get_relay_state)
        self.set_relay_state = Mock(side_effect=self.__mocked_set_relay_state)
        self.__relays = [0] * self.RELAYS_COUNT

    def __mocked_get_relay_state(self, relay_index):
        if relay_index < 0 or relay_index > self.RELAYS_COUNT - 1:
            raise ValueError()
        return self.__relays[relay_index]

    def __mocked_set_relay_state(self, relay_index, state):
        self.__relays[relay_index] = state


class TestProgram(unittest.TestCase):

    def setUp(self):
        self.therm_sensor_api_mock = ThermSensorApiMock()
        self.relay_api_mock = RelayApiMock()

    def test_should_idle_if_temperature_raises_but_is_within_defined_range(self):
        self.givenProgramWithMinMaxTemp(18.0, 18.6)
        self.when_temperature_is(18.5)
        self.then_cooling_is(0)
        self.then_heating_is(0)
        self.when_temperature_is(18.6)
        self.then_cooling_is(0)
        self.then_heating_is(0)

    def test_should_idle_if_temperature_drops_but_is_within_defined_range(self):
        self.givenProgramWithMinMaxTemp(18.0, 18.6)
        self.when_temperature_is(18.1)
        self.then_cooling_is(0)
        self.then_heating_is(0)
        self.when_temperature_is(18.0)
        self.then_cooling_is(0)
        self.then_heating_is(0)

    def test_should_activate_cooling_if_temperature_raises_above_max(self):
        self.givenProgramWithMinMaxTemp(18.0, 18.6)
        self.when_temperature_is(18.60)
        self.then_cooling_is(0)
        self.then_heating_is(0)
        self.when_temperature_is(18.61)
        self.then_cooling_is(1)
        self.then_heating_is(0)
        self.when_temperature_is(18.62)
        self.then_cooling_is(1)
        self.then_heating_is(0)
        self.relay_api_mock.set_relay_state.assert_called_once_with(COOLING_RELAY_INDEX, True)

    def test_should_activate_cooling_if_temperature_raises_above_max_and_deactivate_when_back_to_normal(self):
        self.givenProgramWithMinMaxTemp(18.0, 18.6)
        self.when_temperature_is(18.60)
        self.then_cooling_is(0)
        self.then_heating_is(0)
        self.when_temperature_is(18.61)
        self.then_cooling_is(1)
        self.then_heating_is(0)
        self.when_temperature_is(18.60)
        self.then_cooling_is(0)
        self.then_heating_is(0)

    def test_should_activate_heating_if_temperature_drops_below_min(self):
        self.givenProgramWithMinMaxTemp(18.0, 18.6)
        self.when_temperature_is(18.0)
        self.then_cooling_is(0)
        self.then_heating_is(0)
        self.when_temperature_is(17.99)
        self.then_cooling_is(0)
        self.then_heating_is(1)
        self.when_temperature_is(17.98)
        self.then_cooling_is(0)
        self.then_heating_is(1)
        self.relay_api_mock.set_relay_state.assert_called_once_with(HEATING_RELAY_INDEX, True)

    def test_should_activate_heating_if_temperature_drops_below_min_and_deactivate_when_back_to_normal(self):
        self.givenProgramWithMinMaxTemp(18.0, 18.6)
        self.when_temperature_is(18.0)
        self.then_cooling_is(0)
        self.then_heating_is(0)
        self.when_temperature_is(17.99)
        self.then_cooling_is(0)
        self.then_heating_is(1)
        self.when_temperature_is(18.0)
        self.then_cooling_is(0)
        self.then_heating_is(0)

    def test_should_not_activate_heating_if_temperature_drops_below_min_but_heating_not_available(self):
        self.givenProgramWithMinMaxTemp(18.0, 18.6, heating=False, cooling=True)
        self.when_temperature_is(18.0)
        self.then_cooling_is(0)
        self.then_heating_is(0)
        self.when_temperature_is(17.99)
        self.then_cooling_is(0)
        self.then_heating_is(0)

    def test_should_not_activate_cooling_if_temperature_raises_above_max_but_cooling_not_available(self):
        self.givenProgramWithMinMaxTemp(18.0, 18.6, heating=True, cooling=False)
        self.when_temperature_is(18.60)
        self.then_cooling_is(0)
        self.then_heating_is(0)
        self.when_temperature_is(18.61)
        self.then_cooling_is(0)
        self.then_heating_is(0)

    def test_should_stop_controlling_cooling_when_program_gets_deactivated(self):
        self.givenProgramWithMinMaxTemp(18.0, 18.6, active=True)
        self.when_temperature_is(18.6)
        self.then_cooling_is(0)
        self.then_heating_is(0)
        self.when_temperature_is(18.61)
        self.then_cooling_is(1)
        self.then_heating_is(0)
        self.when_temperature_is(18.60)
        self.then_cooling_is(0)
        self.then_heating_is(0)
        self.when_program_deactivated()
        self.when_temperature_is(18.61)
        self.then_cooling_is(0)
        self.then_heating_is(0)

    def test_should_stop_controlling_heating_when_program_gets_deactivated(self):
        self.givenProgramWithMinMaxTemp(18.0, 18.6)
        self.when_temperature_is(18.0)
        self.then_cooling_is(0)
        self.then_heating_is(0)
        self.when_temperature_is(17.99)
        self.then_cooling_is(0)
        self.then_heating_is(1)
        self.when_temperature_is(18.0)
        self.then_cooling_is(0)
        self.then_heating_is(0)
        self.when_program_deactivated()
        self.when_temperature_is(17.99)
        self.then_cooling_is(0)
        self.then_heating_is(0)

    def test_should_start_controlling_cooling_when_program_gets_activated(self):
        self.givenProgramWithMinMaxTemp(18.0, 18.6, active=False)
        self.when_temperature_is(18.6)
        self.then_cooling_is(0)
        self.then_heating_is(0)
        self.when_temperature_is(18.61)
        self.then_cooling_is(0)
        self.then_heating_is(0)
        self.when_temperature_is(18.60)
        self.then_cooling_is(0)
        self.then_heating_is(0)
        self.when_program_activated()
        self.when_temperature_is(18.61)
        self.then_cooling_is(1)
        self.then_heating_is(0)

    def test_should_start_controlling_heating_when_program_gets_activated(self):
        self.givenProgramWithMinMaxTemp(18.0, 18.6, active=False)
        self.when_temperature_is(18.0)
        self.then_cooling_is(0)
        self.then_heating_is(0)
        self.when_temperature_is(17.99)
        self.then_cooling_is(0)
        self.then_heating_is(0)
        self.when_temperature_is(18.0)
        self.then_cooling_is(0)
        self.then_heating_is(0)
        self.when_program_activated()
        self.when_temperature_is(17.99)
        self.then_cooling_is(0)
        self.then_heating_is(1)

    def test_should_deactivate_cooling_when_program_gets_deactivated(self):
        self.givenProgramWithMinMaxTemp(18.0, 18.6, active=True)
        self.when_temperature_is(18.6)
        self.then_cooling_is(0)
        self.then_heating_is(0)
        self.when_temperature_is(18.61)
        self.then_cooling_is(1)
        self.then_heating_is(0)
        self.when_program_deactivated()
        self.then_cooling_is(0)
        self.then_heating_is(0)

    def test_should_deactivate_heating_when_program_gets_deactivated(self):
        self.givenProgramWithMinMaxTemp(18.0, 18.6, active=True)
        self.when_temperature_is(18.0)
        self.then_cooling_is(0)
        self.then_heating_is(0)
        self.when_temperature_is(17.99)
        self.then_cooling_is(0)
        self.then_heating_is(1)
        self.when_program_deactivated()
        self.then_cooling_is(0)
        self.then_heating_is(0)

    def test_should_get_cooling_back_to_correct_state_when_program_was_activated_in_unusual_state(self):
        self.givenProgramWithMinMaxTemp(18.0, 18.6, active=False)
        self.when_temperature_is(18.5)
        # Cooling was being activated when program got resumed
        self.relay_api_mock.set_relay_state(COOLING_RELAY_INDEX, True)
        self.when_program_activated()
        self.then_cooling_is(0)
        self.then_heating_is(0)

    def test_program_should_skip_update_if_sensor_is_not_ready(self):
        self.givenProgramWithMinMaxTemp(18.0, 18.4)
        # None temperature will raise SensorNotReadyError
        self.when_temperature_is(None)
        self.then_cooling_is(0)
        self.then_heating_is(0)
        self.when_temperature_is(18.5)
        self.then_cooling_is(1)
        self.then_heating_is(0)

    def test_program_should_deactivate_if_during_update_sensor_was_not_found(self):
        self.givenProgramWithMinMaxTemp(18.0, 18.4)
        self.when_temperature_is(18.5)
        self.then_cooling_is(1)
        self.then_heating_is(0)
        # Trying to read temperature that is not available will raise NoSensorFoundError
        self.therm_sensor_api_mock.unset_temperature(SENSOR_ID)
        self.program.update()
        self.assertEqual(self.program.active, False)
        self.then_cooling_is(0)
        self.then_heating_is(0)

    def test_program_should_serialize_to_json(self):
        self.givenProgramWithMinMaxTemp(18.0, 18.6)
        json_str = self.program.to_json()
        parsed_json = json.loads(json_str)
        self.assertEqual(parsed_json["sensor_id"], SENSOR_ID)
        self.assertEqual(parsed_json["heating_relay_index"], HEATING_RELAY_INDEX)
        self.assertEqual(parsed_json["cooling_relay_index"], COOLING_RELAY_INDEX)
        self.assertEqual(parsed_json["min_temp"], 18.0)
        self.assertEqual(parsed_json["max_temp"], 18.6)
        self.assertEqual(parsed_json["active"], True)

        self.givenProgramWithMinMaxTemp(18.1, 18.5, heating=False, cooling=False, active=False)
        json_str = self.program.to_json()
        parsed_json = json.loads(json_str)
        self.assertEqual(parsed_json["sensor_id"], SENSOR_ID)
        self.assertEqual(parsed_json["heating_relay_index"], -1)
        self.assertEqual(parsed_json["cooling_relay_index"], -1)
        self.assertEqual(parsed_json["min_temp"], 18.1)
        self.assertEqual(parsed_json["max_temp"], 18.5)
        self.assertEqual(parsed_json["active"], False)

    def test_program_should_deserialize_from_json(self):
        json_data = {"sensor_id": "1001",
                     "heating_relay_index": 2,
                     "cooling_relay_index": 7,
                     "min_temp": 17.5,
                     "max_temp": 18.4,
                     "active": True}
        json_str = json.dumps(json_data)
        program = Program.from_json(json_str)
        self.assertEqual(program.sensor_id, "1001")
        self.assertEqual(program.heating_relay_index, 2)
        self.assertEqual(program.cooling_relay_index, 7)
        self.assertEqual(program.min_temperature, 17.5)
        self.assertEqual(program.max_temperature, 18.4)
        self.assertEqual(program.active, True)

        json_data = {"sensor_id": "1002",
                     "heating_relay_index": -1,
                     "cooling_relay_index": -1,
                     "min_temp": 17.2,
                     "max_temp": 18.3,
                     "active": False}
        json_str = json.dumps(json_data)
        program = Program.from_json(json_str)
        self.assertEqual(program.sensor_id, "1002")
        self.assertEqual(program.heating_relay_index, -1)
        self.assertEqual(program.cooling_relay_index, -1)
        self.assertEqual(program.min_temperature, 17.2)
        self.assertEqual(program.max_temperature, 18.3)
        self.assertEqual(program.active, False)

    def givenProgramWithMinMaxTemp(self, min_temp, max_temp, heating=True, cooling=True, active=True):
        self.program = Program(SENSOR_ID,
                               HEATING_RELAY_INDEX if heating else -1,
                               COOLING_RELAY_INDEX if cooling else -1,
                               min_temp, max_temp,
                               therm_sensor_api=self.therm_sensor_api_mock,
                               relay_api=self.relay_api_mock,
                               active=active)

    def when_temperature_is(self, temperature):
        self.therm_sensor_api_mock.set_temperature(SENSOR_ID, temperature)
        self.program.update()

    def when_program_deactivated(self):
        self.program.active = False

    def when_program_activated(self):
        self.program.active = True

    def then_heating_is(self, relay_state):
        self.assertEqual(self.relay_api_mock.get_relay_state(HEATING_RELAY_INDEX), relay_state)

    def then_cooling_is(self, relay_state):
        self.assertEqual(self.relay_api_mock.get_relay_state(COOLING_RELAY_INDEX), relay_state)

