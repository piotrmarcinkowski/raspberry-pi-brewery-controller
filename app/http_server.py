import json

from flask import Flask
import threading
import sys

from app.controller import Controller

this_module = sys.modules[__name__]
__controller: Controller = None
__server_running = False
app = Flask("BreweryRestAPI")
URL_PATH = "/brewery/api/v1.0/"
URL_RESOURCE_SENSORS = "therm_sensors"


@app.route(URL_PATH + URL_RESOURCE_SENSORS, methods=['GET'])
def get_therm_sensors():
    sensors = __controller.get_therm_sensors()
    response = []
    for sensor in sensors:
        response.append({"id": sensor.id, "name": sensor.name})
    return json.dumps(response)


def start_server():
    if this_module.__server_running:
        raise RuntimeError("Server already running")
    app.run(debug=False, use_reloader=False)


def start_server_in_separate_thread():
    if this_module.__server_running:
        raise RuntimeError("Server already running")
    threading.Thread(target=start_server).start()


def init(controller: Controller):
    this_module.__controller = controller
