import unittest

from app.hardware.therm_sensor_api import NoSensorFoundError
from mocks import ThermSensorApiMock, RelayApiMock
from monitor import Monitor
from program import Program

SENSOR_ID = "sensor_id"
PROGRAM_ID = "11111111-abcd-abcd-2222-333333333333"
PROGRAM_NAME = "test name"
HEATING_RELAY_INDEX = 1
COOLING_RELAY_INDEX = 2


class TestMonitor(unittest.TestCase):

    def setUp(self):
        self.therm_sensor_api_mock = ThermSensorApiMock()
        self.relay_api_mock = RelayApiMock()
        pass

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
        self.givenProgramWithMinMaxTemp(18.0, 18.6, heating=False, active=False)
        self.when_temperature_is(17.0)
        # Cooling was active when program got resumed, that should not happen
        # The temperature is way to low, monitor should deactivate cooling immediately
        self.relay_api_mock.set_relay_state(COOLING_RELAY_INDEX, 1)
        self.when_program_activated()
        self.then_cooling_is(0)
        self.then_heating_is(0)

    def test_should_get_heating_back_to_correct_state_when_program_was_activated_in_unusual_state(self):
        self.givenProgramWithMinMaxTemp(18.0, 18.6, cooling=False, active=False)
        self.when_temperature_is(19.0)
        # Heating was active when program got resumed, that should not happen
        # The temperature is way to high, monitor should deactivate heating immediately
        self.relay_api_mock.set_relay_state(HEATING_RELAY_INDEX, 1)
        self.when_program_activated()
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
        self.when_temperature_is(18.3)
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
        self.then_cooling_is(1)
        self.then_heating_is(0)
        self.when_temperature_is(18.31)
        self.then_cooling_is(1)
        self.then_heating_is(0)
        self.when_temperature_is(18.30)
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
        self.then_heating_is(1)
        self.when_temperature_is(18.29)
        self.then_cooling_is(0)
        self.then_heating_is(1)
        self.when_temperature_is(18.30)
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
        self.when_temperature_is(18.3)
        self.then_cooling_is(0)
        self.then_heating_is(0)
        self.when_program_deactivated()
        self.when_temperature_is(18.61)
        self.then_cooling_is(0)
        self.then_heating_is(0)

    def test_monitor_should_skip_update_if_sensor_is_not_ready(self):
        self.givenProgramWithMinMaxTemp(18.0, 18.4)
        # None temperature will raise SensorNotReadyError
        self.when_temperature_is(None)
        self.then_cooling_is(0)
        self.then_heating_is(0)
        self.when_temperature_is(18.5)
        self.then_cooling_is(1)
        self.then_heating_is(0)

    def test_monitor_should_deactivate_relays_and_raise_error_if_during_check_sensor_was_not_found(self):
        self.givenProgramWithMinMaxTemp(18.0, 18.4)
        self.when_temperature_is(18.5)
        self.then_cooling_is(1)
        self.then_heating_is(0)
        # Trying to read temperature from non-existing sensor will raise NoSensorFoundError
        self.when_sensor_was_detached()
        self.monitor.check()
        self.then_error_is(NoSensorFoundError)
        self.then_cooling_is(0)
        self.then_heating_is(0)

    def test_monitor_should_resume_temperature_controlling_and_remove_error_if_sensor_was_found_again(self):
        self.givenProgramWithMinMaxTemp(18.0, 18.4)
        self.when_temperature_is(18.5)
        self.then_cooling_is(1)
        self.then_heating_is(0)
        # Trying to read temperature from non-existing sensor will raise NoSensorFoundError
        self.when_sensor_was_detached()
        self.monitor.check()
        self.then_error_is(NoSensorFoundError)
        self.then_cooling_is(0)
        self.then_heating_is(0)
        self.when_temperature_is(18.5)
        self.then_cooling_is(1)
        self.then_heating_is(0)
        self.then_error_is(None)

    def test_monitor_should_leave_relays_deactivated_and_keep_error_raised_after_attempt_to_activate_with_missing_sensor(self):
        self.givenProgramWithMinMaxTemp(18.0, 18.4)
        self.when_temperature_is(18.5)
        self.then_cooling_is(1)
        self.then_heating_is(0)
        # Trying to read temperature from non-existing sensor will raise NoSensorFoundError
        self.when_sensor_was_detached()
        self.monitor.check()
        # Try to check again
        self.monitor.check()
        self.then_error_is(NoSensorFoundError)
        self.then_cooling_is(0)
        self.then_heating_is(0)

    def givenProgramWithMinMaxTemp(self, min_temp, max_temp, heating=True, cooling=True, active=True):
        self.program = Program(PROGRAM_ID, PROGRAM_NAME,
                               SENSOR_ID,
                               HEATING_RELAY_INDEX if heating else -1,
                               COOLING_RELAY_INDEX if cooling else -1,
                               min_temp, max_temp,
                               active=active)
        self.monitor = Monitor(self.program, self.therm_sensor_api_mock, self.relay_api_mock)

    def when_temperature_is(self, temperature):
        self.therm_sensor_api_mock.mock_sensors_temperature({SENSOR_ID: temperature})
        self.monitor.check()

    def when_sensor_was_detached(self):
        self.therm_sensor_api_mock.mock_sensors_temperature({})

    def when_program_deactivated(self):
        self.program = self.program.modify_with(self.program, active=False)
        self.monitor = Monitor(self.program, self.therm_sensor_api_mock, self.relay_api_mock)
        self.monitor.check()

    def when_program_activated(self):
        self.program = self.program.modify_with(self.program, active=True)
        self.monitor = Monitor(self.program, self.therm_sensor_api_mock, self.relay_api_mock)
        self.monitor.check()

    def then_heating_is(self, relay_state):
        self.assertEqual(relay_state, self.relay_api_mock.get_relay_state(HEATING_RELAY_INDEX))

    def then_cooling_is(self, relay_state):
        self.assertEqual(relay_state, self.relay_api_mock.get_relay_state(COOLING_RELAY_INDEX))

    def then_error_is(self, error_type):
        if error_type is None:
            self.assertIsNone(self.monitor.get_error())
        else:
            self.assertEqual(error_type, type(self.monitor.get_error()))
