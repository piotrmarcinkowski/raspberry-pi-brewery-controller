import unittest
from unittest.mock import Mock
import RPi

from app.hardware.relay_api import RelayApi


def gpio_input(gpio_channel):
    return 1


class RelayApiTest(unittest.TestCase):

    def setUp(self):
        pass

    def mock_relay_states(self):
        RPi.GPIO.input = Mock(side_effect=gpio_input())

    def test_should_return_proper_relay_state(self):
        api = RelayApi()
        relay_state = api.get_relay_state(0)
        self.assertEqual(relay_state, 1)

