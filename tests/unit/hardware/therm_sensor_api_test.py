import unittest
from unittest.mock import Mock

from w1thermsensor import W1ThermSensor

from app.hardware.therm_sensor_api import ThermSensorApi


class ThermSensorApiTestCase(unittest.TestCase):

    def test_should_return_proper_id_list(self):
        sensor1 = Mock(spec=W1ThermSensor)
        sensor1.id = '100001'
        sensor2 = Mock(spec=W1ThermSensor)
        sensor2.id = '100002'
        sensor3 = Mock(spec=W1ThermSensor)
        sensor3.id = '100003'
        mocked_sensors = [sensor1, sensor2, sensor3]
        W1ThermSensor.get_available_sensors = Mock(return_value=mocked_sensors)

        api = ThermSensorApi()
        detected_sensors = api.get_sensor_id_list()

        W1ThermSensor.get_available_sensors.assert_called_once()
        self.assertEqual(len(detected_sensors), len(mocked_sensors))
        self.assertEqual(detected_sensors[0], '100001')
        self.assertEqual(detected_sensors[1], '100002')
        self.assertEqual(detected_sensors[2], '100003')


if __name__ == '__main__':
    unittest.main()
