import os
import json
from pathlib import Path
from app.program import Program
from app.therm_sensor import ThermSensor


def get_home_dir_path():
    return str(Path.home())


def get_storage_root_dir_path():
    return os.path.join(get_home_dir_path(), ".brewery")


class Storage(object):
    """
    Use to persistently store data, eg. configuration
    """

    def __init__(self, storage_root_dir=get_storage_root_dir_path(),
                 programs_file_name="programs", sensors_file_name="sensors"):
        super().__init__()
        self.storage_root_dir = storage_root_dir
        self.programs_file = programs_file_name
        self.sensors_file = sensors_file_name

    def store_programs(self, programs):
        json_data = [program.to_json_data() for program in programs]
        self.__write_json_data_to_file(self.programs_file, json_data)

    def load_programs(self):
        input_file = os.path.join(self.storage_root_dir, self.programs_file)
        if os.path.exists(input_file):
            with open(input_file, "r") as file:
                json_input = file.read()
                json_data = json.loads(json_input)
                return [Program.from_json_data(json_data[index]) for index in range(len(json_data))]
        else:
            return []

    def store_sensors(self, sensors):
        json_data = [sensor.to_json_data() for sensor in sensors]
        self.__write_json_data_to_file(self.sensors_file, json_data)

    def load_sensors(self):
        input_file = os.path.join(self.storage_root_dir, self.sensors_file)
        if os.path.exists(input_file):
            with open(input_file, "r") as file:
                json_input = file.read()
                json_data = json.loads(json_input)
                return [ThermSensor.from_json_data(json_data[index]) for index in range(len(json_data))]
        else:
            return []

    def __write_json_data_to_file(self, file, json_data):
        self.__create_root_dir_if_needed()
        output_file = os.path.join(self.storage_root_dir, file)
        json_output = json.dumps(json_data)
        # TODO: For safety write to temp file first, then replace
        with open(output_file, "w") as file:
            file.write(json_output)

    def __create_root_dir_if_needed(self):
        if not os.path.exists(self.storage_root_dir):
            os.makedirs(self.storage_root_dir)
