import sys
import unittest
import random
from unittest.mock import Mock
import RPi
from app.hardware.relay_api import RelayApi

this_module = sys.modules[__name__]
RELAY_GPIO_CHANNELS = [17, 27, 22, 23, 24, 25, 16, 26]
gpio_states = {}


def set_up_random_gpio_input_states():
    this_module.gpio_states = {RELAY_GPIO_CHANNELS[index]: random.randint(0, 1) for index in range(len(RELAY_GPIO_CHANNELS))}


def gpio_input(gpio_channel):
    return gpio_states[gpio_channel]


def reversed_state(state):
    return abs(state - 1)


class RelayApiTest(unittest.TestCase):

    def setUp(self):
        set_up_random_gpio_input_states()
        self.mock_relay_states()
        pass

    def mock_relay_states(self):
        RPi.GPIO.setmode = Mock()
        RPi.GPIO.setup = Mock()
        RPi.GPIO.input = Mock(side_effect=gpio_input)
        RPi.GPIO.output = Mock()

    def test_should_initialize_with_high_state_for_low_voltage_control_relay(self):
        api = RelayApi(low_voltage_control=True)

        RPi.GPIO.setmode.assert_called_with(RPi.GPIO.BCM)
        RPi.GPIO.setup.assert_called_with(RELAY_GPIO_CHANNELS, RPi.GPIO.OUT, initial=RPi.GPIO.HIGH)

    def test_should_initialize_with_high_state_for_high_voltage_control_relay(self):
        api = RelayApi(low_voltage_control=False)

        RPi.GPIO.setmode.assert_called_with(RPi.GPIO.BCM)
        RPi.GPIO.setup.assert_called_with(RELAY_GPIO_CHANNELS, RPi.GPIO.OUT, initial=RPi.GPIO.LOW)

    def test_should_return_proper_relay_state_for_low_voltage_control_relay(self):
        api = RelayApi(low_voltage_control=True)

        relays_count = len(RELAY_GPIO_CHANNELS)
        for relay_index in range(relays_count):
            relay_state = api.get_relay_state(relay_index)
            self.assertEqual(relay_state, reversed_state(gpio_states[RELAY_GPIO_CHANNELS[relay_index]]))

    def test_should_return_proper_relay_state_for_high_voltage_control_relay(self):
        api = RelayApi(low_voltage_control=False)

        relays_count = len(RELAY_GPIO_CHANNELS)
        for relay_index in range(relays_count):
            relay_state = api.get_relay_state(relay_index)
            self.assertEqual(relay_state, gpio_states[RELAY_GPIO_CHANNELS[relay_index]])

    def test_should_raise_error_when_getting_relay_with_invalid_index(self):
        api = RelayApi()

        with (self.assertRaises(ValueError)):
            api.get_relay_state(-1)

        with (self.assertRaises(ValueError)):
            api.get_relay_state(100)

    def test_should_set_proper_relay_state_for_low_voltage_control_relay(self):
        api = RelayApi(low_voltage_control=True)

        relays_count = len(RELAY_GPIO_CHANNELS)
        # generate random states to set
        relay_states = [random.randint(0, 1) for _ in range(len(RELAY_GPIO_CHANNELS))]
        for relay_index in range(relays_count):
            api.set_relay_state(relay_index, relay_states[relay_index])
            RPi.GPIO.output.assert_called_with(RELAY_GPIO_CHANNELS[relay_index], reversed_state(relay_states[relay_index]))

    def test_should_set_proper_relay_state_for_high_voltage_control_relay(self):
        api = RelayApi(low_voltage_control=False)

        relays_count = len(RELAY_GPIO_CHANNELS)
        # generate random states to set
        relay_states = [random.randint(0, 1) for _ in range(len(RELAY_GPIO_CHANNELS))]
        for relay_index in range(relays_count):
            api.set_relay_state(relay_index, relay_states[relay_index])
            RPi.GPIO.output.assert_called_with(RELAY_GPIO_CHANNELS[relay_index], relay_states[relay_index])

    def test_should_raise_error_when_setting_relay_with_invalid_index(self):
        api = RelayApi()

        with (self.assertRaises(ValueError)):
            api.set_relay_state(-1, 0)

        with (self.assertRaises(ValueError)):
            api.set_relay_state(100, 0)

    def test_should_raise_error_when_setting_relay_to_invalid_state(self):
        api = RelayApi()

        with (self.assertRaises(ValueError)):
            api.set_relay_state(0, -1)

        with (self.assertRaises(ValueError)):
            api.set_relay_state(0, 2)
