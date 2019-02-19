import json

from flask import Flask, Response, abort
import threading
import sys

from app.controller import Controller
from hardware.therm_sensor_api import NoSensorFoundError, SensorNotReadyError

this_module = sys.modules[__name__]
__controller = None
__server_running = False
app = Flask("BreweryRestAPI")
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 80
URL_PATH = "/brewery/api/v1.0/"
URL_RESOURCE_SENSORS = "therm_sensors"


@app.route(URL_PATH + URL_RESOURCE_SENSORS, methods=['GET'])
def get_therm_sensors():
    sensors = __controller.get_therm_sensors()
    response = []
    for sensor in sensors:
        response.append({"id": sensor.id, "name": sensor.name})
    return valid_request_response(json.dumps(response))


@app.route(URL_PATH + URL_RESOURCE_SENSORS + "/<sensor_id>", methods=['GET'])
def get_therm_sensor_temperature(sensor_id):
    try:
        temperature = __controller.get_therm_sensor_temperature(sensor_id)
        response = {"id": sensor_id, "temperature": temperature}
        return valid_request_response(json.dumps(response))
    except NoSensorFoundError:
        return invalid_request_response(404)
    except SensorNotReadyError:
        return invalid_request_response(403)


def valid_request_response(content):
    return Response(content, content_type="text/json")


def invalid_request_response(status, content=""):
    return Response(content, status=status, content_type="text/json")


def start_server():
    if this_module.__server_running:
        raise RuntimeError("Server already running")
    app.run(debug=False, use_reloader=False, host=SERVER_HOST, port=SERVER_PORT)


def start_server_in_separate_thread():
    if this_module.__server_running:
        raise RuntimeError("Server already running")
    threading.Thread(target=start_server).start()


def init(controller: Controller):
    this_module.__controller = controller
