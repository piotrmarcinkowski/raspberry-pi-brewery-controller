import unittest
import uuid
import os
from pathlib import Path

from app.program import Program
from app.storage import Storage
from app.therm_sensor import ThermSensor


class StorageTestCase(unittest.TestCase):

    def setUp(self):
        self.home_dir = str(Path.home())
        self.root_dir = os.path.join(self.home_dir, ".brewery")
        self.programs_filename = str(uuid.uuid4())
        self.programs_file_path = os.path.join(self.root_dir, self.programs_filename)
        self.sensors_filename = str(uuid.uuid4())
        self.sensors_file_path = os.path.join(self.root_dir, self.sensors_filename)

    def tearDown(self):
        try:
            os.remove(self.programs_file_path)
            os.remove(self.sensors_file_path)
            os.rmdir(self.root_dir)
        except FileNotFoundError:
            return

    def test_should_store_programs_to_file_and_be_able_to_load_it_back(self):
        programs = [
            Program("id1", "program1", "sensor1", 1, 2, 16.7, 18.9),
            Program("id2", "program2", "sensor2", 4, -1, 14.0, 15.0, active=False)
        ]
        storage = self.__create_storage()
        storage.store_programs(programs)

        storage2 = self.__create_storage()
        loaded_programs = storage2.load_programs()

        for index in range(len(loaded_programs)):
            self.assertEqual(loaded_programs[index], programs[index])

    def test_should_return_empty_program_list_if_not_yet_saved(self):
        storage = self.__create_storage()
        loaded_programs = storage.load_programs()

        self.assertEqual(len(loaded_programs), 0)

    def test_should_store_sensor_name_to_file_and_be_able_to_load_it_back(self):
        sensors = [
            ThermSensor("id1", "sensor1"),
            ThermSensor("id2", "sensor2"),
        ]

        storage1 = self.__create_storage()
        storage1.store_sensors(sensors)

        storage2 = self.__create_storage()
        loaded_sensors = storage2.load_sensors()

        self.assertEqual(loaded_sensors, sensors)

    def test_should_return_empty_sensor_list_if_not_yet_saved(self):
        storage = self.__create_storage()
        self.assertEqual(storage.load_sensors(), [])

    def __create_storage(self):
        return Storage(storage_root_dir=self.root_dir,
                       programs_file_name=self.programs_filename,
                       sensors_file_name=self.sensors_filename)
