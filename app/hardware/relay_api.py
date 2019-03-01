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
        :raises ValueError When relay_index is invalid
        """
        if relay_index not in range(len(self.RELAY_GPIO_CHANNELS)):
            raise ValueError("Invalid relay index: {}".format(relay_index))
        gpio = self.RELAY_GPIO_CHANNELS[relay_index]
        return GPIO.input(gpio)

    def set_relay_state(self, relay_index, state):
        """
        Sets the state of given relay
        :param relay_index: Index of the relay
        :type relay_index: int
        :param state: State of the relay. Allowed values are 0 and 1
        :type state: int
        :rtype: int
        :raises ValueError When relay_index is invalid
        :raises ValueError When state is not either 0 or 1
        """
        if relay_index not in range(len(self.RELAY_GPIO_CHANNELS)):
            raise ValueError("Invalid relay index: {}".format(relay_index))
        if state not in [0,1]:
            raise ValueError("Invalid state value: {}".format(state))
        gpio = self.RELAY_GPIO_CHANNELS[relay_index]
        gpio_value = GPIO.HIGH if state == 1 else GPIO.LOW
        GPIO.output(gpio, gpio_value)
        return GPIO.input(gpio)