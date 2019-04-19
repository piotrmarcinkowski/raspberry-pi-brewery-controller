import app.hardware.hw_config as hw_config
from app.logger import Logger

if hw_config.RUN_ON_RASPBERRY:
    import RPi.GPIO as GPIO


class RelayApi(object):
    RELAY_GPIO_CHANNELS = [17, 27, 22, 23, 24, 25, 16, 26]

    def __init__(self) -> None:
        super().__init__()
        if hw_config.RUN_ON_RASPBERRY:
            self.__init_gpio()
        else:
            self.__fake_gpio_states = [0, 0, 0, 0, 0, 0, 0, 0]

    def __init_gpio(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.RELAY_GPIO_CHANNELS, GPIO.OUT, initial=GPIO.HIGH)

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
        if hw_config.RUN_ON_RASPBERRY:
            gpio = self.RELAY_GPIO_CHANNELS[relay_index]
            return GPIO.input(gpio) == GPIO.LOW
        else:
            return self.__fake_gpio_states[relay_index]

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
        if state not in [0, 1]:
            raise ValueError("Invalid state value: {}".format(state))
        if hw_config.RUN_ON_RASPBERRY:
            gpio = self.RELAY_GPIO_CHANNELS[relay_index]
            gpio_state = GPIO.LOW if state == 1 else GPIO.HIGH
            GPIO.output(gpio, gpio_state)
            gpio_read_state = GPIO.input(gpio)
            Logger.info("GPIO {} state set:{} read:{}".format(gpio, gpio_state, gpio_read_state))
            return gpio_read_state
        else:
            self.__fake_gpio_states[relay_index] = state
