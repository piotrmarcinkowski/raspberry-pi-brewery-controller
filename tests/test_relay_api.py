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


class RelayApiTest(unittest.TestCase):

    def setUp(self):
        set_up_random_gpio_input_states()
        self.mock_relay_states()
        pass

    def mock_relay_states(self):
        RPi.GPIO.input = Mock(side_effect=gpio_input)

    def test_should_return_proper_relay_state(self):
        api = RelayApi()

        relays_count = len(RELAY_GPIO_CHANNELS)
        for relay_index in range(relays_count):
            relay_state = api.get_relay_state(relay_index)
            self.assertEqual(relay_state, gpio_states[RELAY_GPIO_CHANNELS[relay_index]])
