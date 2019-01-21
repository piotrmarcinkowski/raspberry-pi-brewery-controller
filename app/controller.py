from app.hardware.therm_sensor_api import ThermSensorApi
from app.therm_sensor import ThermSensor
from app.logger import Logger

class Controller(object):
    __therm_sensor_api: ThermSensorApi = None
    __sensor_list: list = None

    def __init__(self, therm_sensor_api=ThermSensorApi()):
        """
        Creates controller instance.
        :param therm_sensor_api: Api to obtain therm sensors and their measurements
        :type therm_sensor_api: ThermSensorApi
        """
        super().__init__()
        self.__therm_sensor_api = therm_sensor_api

    def run(self):
        """
        Start controller. After this function is called the controller will periodically update active programs to
        maintain requested temperature by turning on/off coolers attached to relays
        """
        Logger.info("Starting controller")
        while True:
            pass
        Logger.info("Controller stopped")

    def get_therm_sensors(self):
        """
        Returns available therm sensors of ThermSensor type
        :return: List of available therm sensors
        :rtype list
        """

        if self.__sensor_list is None:
            sensor_ids = self.__therm_sensor_api.get_sensor_id_list()
            self.__sensor_list = [ThermSensor(sensor_id) for sensor_id in sensor_ids]

        return self.__sensor_list
