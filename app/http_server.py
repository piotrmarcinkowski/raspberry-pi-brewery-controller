import json

from flask import Flask, Response, request
import threading
import sys

from app.controller import Controller, ProgramError
from app.hardware.therm_sensor_api import NoSensorFoundError, SensorNotReadyError
from app.program import Program

this_module = sys.modules[__name__]
__controller = None
__server_running = False
app = Flask("BreweryRestAPI")
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 80
URL_PATH = "/brewery/api/v1.0/"
URL_RESOURCE_SENSORS = "therm_sensors"
URL_RESOURCE_PROGRAMS = "programs"


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
    except NoSensorFoundError as e:
        return invalid_request_response(404, content=str(e))
    except SensorNotReadyError as e:
        return invalid_request_response(403, content=str(e))


@app.route(URL_PATH + URL_RESOURCE_PROGRAMS, methods=['GET', 'POST'])
def programs():
    if request.method == 'GET':
        return get_programs()
    if request.method == 'POST':
        return create_program(request)


def get_programs():
    response = []
    for program in __controller.get_programs():
        response.append(program.to_json_data())
    return valid_request_response(json.dumps(response))


def create_program(req):
    program = Program.from_json(req.json)
    try:
        __controller.create_program(program)
        return valid_request_response()
    except ProgramError as e:
        return invalid_request_response(403, content=str(e))


@app.route(URL_PATH + URL_RESOURCE_PROGRAMS + "/<program_index>", methods=['PUT', 'DELETE'])
def modify_program(program_index):
    if request.method == 'PUT':
        return replace_program(program_index, request)
    if request.method == 'DELETE':
        return delete_program(program_index)


def replace_program(program_index, req):
    program = Program.from_json(req.json)
    try:
        __controller.modify_program(int(program_index), program)
        return valid_request_response()
    except ValueError as e:
        return invalid_request_response(500, content=str(e))
    except ProgramError as e:
        return invalid_request_response(403, content=str(e))


def delete_program(program_index):
    try:
        __controller.delete_program(int(program_index))
        return valid_request_response()
    except ValueError as e:
        return invalid_request_response(500, content=str(e))
    except ProgramError as e:
        return invalid_request_response(403, content=str(e))


def valid_request_response(content=""):
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
