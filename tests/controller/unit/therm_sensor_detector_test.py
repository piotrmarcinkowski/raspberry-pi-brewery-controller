import unittest
from unittest.mock import Mock

from controller.therm_sensor_detector import ThermSensorDetector
from w1thermsensor import W1ThermSensor


class ThermSensorDetectorTestCase(unittest.TestCase):

    def test_should_call_proper_detect_function(self):
        W1ThermSensor.get_available_sensors = Mock()
        detector = ThermSensorDetector()
        sensors = detector.get_sensors()
        W1ThermSensor.get_available_sensors.assert_called_once()


if __name__ == '__main__':
    unittest.main()
