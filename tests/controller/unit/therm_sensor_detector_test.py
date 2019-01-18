import unittest
from unittest.mock import Mock
from controller.therm_sensor_detector import ThermSensorDetector
from w1thermsensor import W1ThermSensor


class ThermSensorDetectorTestCase(unittest.TestCase):

    def test_should_return_available_sensors(self):
        sensor1 = Mock(spec=W1ThermSensor)
        sensor1.id = '100001'
        sensor2 = Mock(spec=W1ThermSensor)
        sensor2.id = '100002'
        sensor3 = Mock(spec=W1ThermSensor)
        sensor3.id = '100003'
        mocked_sensors = [sensor1, sensor2, sensor3]
        W1ThermSensor.get_available_sensors = Mock(return_value=mocked_sensors)

        detector = ThermSensorDetector()
        returned_sensors = detector.get_sensors()

        W1ThermSensor.get_available_sensors.assert_called_once()
        self.assertEqual(len(returned_sensors), len(mocked_sensors))
        self.assertEqual(returned_sensors[0].id, '100001')
        self.assertEqual(returned_sensors[1].id, '100002')
        self.assertEqual(returned_sensors[2].id, '100003')


if __name__ == '__main__':
    unittest.main()
