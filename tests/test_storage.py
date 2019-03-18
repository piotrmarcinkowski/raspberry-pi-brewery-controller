import unittest
import uuid
import os
from pathlib import Path

from app.program import Program
from app.storage import Storage


class StorageTestCase(unittest.TestCase):

    def setUp(self):
        self.home_dir = str(Path.home())
        self.root_dir = os.path.join(self.home_dir, ".brewery")
        self.programs_filename = str(uuid.uuid4())
        self.programs_file_path = os.path.join(self.root_dir, self.programs_filename)

    def tearDown(self):
        try:
            os.remove(self.programs_file_path)
            os.rmdir(self.root_dir)
        except FileNotFoundError:
            return

    def test_should_store_programs_to_file_and_be_able_to_load_it_back(self):
        programs = [
            Program("id1", 1, 2, 16.7, 18.9),
            Program("id2", 4, -1, 14.0, 15.0, active=False)
        ]
        storage = Storage(storage_root_dir=self.root_dir, programs_file_name=self.programs_filename)
        storage.store_programs(programs)

        storage2 = Storage(storage_root_dir=self.root_dir, programs_file_name=self.programs_filename)
        loaded_programs = storage2.load_programs()

        for index in range(len(loaded_programs)):
            self.assertEqual(loaded_programs[index], programs[index])

    def test_should_return_empty_program_list_if_not_yet_saved(self):
        storage = Storage(storage_root_dir=self.root_dir, programs_file_name=self.programs_filename)
        loaded_programs = storage.load_programs()

        self.assertEqual(len(loaded_programs), 0)
