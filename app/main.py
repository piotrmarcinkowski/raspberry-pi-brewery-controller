from app.controller import Controller
import app.http_server as server

import app.hardware.hw_config as hw_config
from program import Program
from storage import Storage

if hw_config.RUN_ON_RASPBERRY:
    from app.hardware.therm_sensor_api import ThermSensorApi
    from app.hardware.relay_api import RelayApi
else:
    from app.hardware.fake_hw import FakeHardware


def main():
    if hw_config.RUN_ON_RASPBERRY:
        therm_sensor_api = ThermSensorApi()
        relay_api = RelayApi()
        storage = Storage()
    else:
        fake_hw = FakeHardware()
        therm_sensor_api = fake_hw.therm_sensor_api
        relay_api = fake_hw.relay_api
        storage = fake_hw.storage

    controller = Controller(therm_sensor_api, relay_api, storage)
    server.init(controller)
    server.start_server_in_separate_thread()
    controller.run()


if __name__ == '__main__':
    main()
