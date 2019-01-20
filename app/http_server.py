from flask import Flask
import threading
import sys

this_module = sys.modules[__name__]
controller = None
app = Flask("BreweryRestAPI")
URL_PATH = "/brewery/api/v1.0/"
URL_RESOURCE_SENSORS = "therm_sensors"


@app.route(URL_PATH + URL_RESOURCE_SENSORS, methods=['GET'])
def get_therm_sensors():
    return """
        "sensors" : []
    """


def start_server(controller):
    if this_module.controller is not None:
        raise RuntimeError("Server already running")
    this_module.controller = controller
    app.run(debug=False, use_reloader=False)


def start_server_in_separate_thread(controller):
    if this_module.controller is not None:
        raise RuntimeError("Server already running")
    threading.Thread(target=start_server, args=(controller,)).start()
