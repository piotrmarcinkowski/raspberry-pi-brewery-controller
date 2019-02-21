import RPi.GPIO as GPIO


class RelayApi(object):
    RELAY_GPIO_CHANNELS = [17, 27, 22, 23, 24, 25, 16, 26]

    def __init__(self) -> None:
        super().__init__()
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.RELAY_GPIO_CHANNELS, GPIO.OUT, initial=GPIO.LOW)

    def get_relay_state(self, relay_index):
        """
        Returns current state of given relay
        :param relay_index: Index of the relay
        :type relay_index: int
        :returns: current state of given relay 0|1
        :rtype: int
        """
        gpio = self.RELAY_GPIO_CHANNELS[relay_index]
        return GPIO.input(gpio)
