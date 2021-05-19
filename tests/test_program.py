import unittest
import json
import uuid
from app.program import Program

SENSOR_ID = "sensor_id"
PROGRAM_ID = "11111111-abcd-abcd-2222-333333333333"
PROGRAM_NAME = "test name"
HEATING_RELAY_INDEX = 1
COOLING_RELAY_INDEX = 2

class TestProgram(unittest.TestCase):

    def setUp(self):
        pass

    def test_program_should_serialize_to_json(self):
        program_id = str(uuid.uuid4())
        self.program = Program(program_id=program_id,
                               program_name="program1",
                               sensor_id="sensor123abc",
                               heating_relay_index=2,
                               cooling_relay_index=3,
                               min_temperature=18.0,
                               max_temperature=18.6,
                               active=True)
        json_str = self.program.to_json()
        parsed_json = json.loads(json_str)
        self.assertEqual(program_id, parsed_json["id"])
        self.assertEqual("program1", parsed_json["name"])
        self.assertNotEqual("", parsed_json["crc"])
        self.assertEqual("sensor123abc", parsed_json["sensor_id"])
        self.assertEqual(2, parsed_json["heating_relay_index"])
        self.assertEqual(3, parsed_json["cooling_relay_index"])
        self.assertEqual(18.0, parsed_json["min_temp"])
        self.assertEqual(18.6, parsed_json["max_temp"])
        self.assertEqual(True, parsed_json["active"])
        crc1 = parsed_json["crc"]

        program_id = str(uuid.uuid4())
        self.program = Program(program_id=program_id,
                               program_name="program2",
                               sensor_id="sensorabc123",
                               heating_relay_index=-1,
                               cooling_relay_index=-1,
                               min_temperature=18.1,
                               max_temperature=18.5,
                               active=False)
        json_str = self.program.to_json()
        parsed_json = json.loads(json_str)
        self.assertEqual(program_id, parsed_json["id"])
        self.assertEqual("program2", parsed_json["name"])
        self.assertNotEqual("", parsed_json["crc"])
        self.assertNotEqual(crc1, parsed_json["crc"])
        self.assertEqual("sensorabc123", parsed_json["sensor_id"])
        self.assertEqual(-1, parsed_json["heating_relay_index"])
        self.assertEqual(-1, parsed_json["cooling_relay_index"])
        self.assertEqual(18.1, parsed_json["min_temp"])
        self.assertEqual(18.5, parsed_json["max_temp"])
        self.assertEqual(False, parsed_json["active"])

    def test_program_should_deserialize_from_json(self):
        program_id = str(uuid.uuid4())
        json_data = {"id": program_id,
                     "name": "program1",
                     "crc": "crc1",
                     "sensor_id": "1002",
                     "heating_relay_index": 2,
                     "cooling_relay_index": 7,
                     "min_temp": 17.5,
                     "max_temp": 18.4,
                     "active": True}
        json_str = json.dumps(json_data)
        program = Program.from_json(json_str)
        self.assertEqual(program_id, program.program_id)
        self.assertEqual("program1", program.program_name)
        self.assertEqual("1002", program.sensor_id)
        self.assertEqual(2, program.heating_relay_index)
        self.assertEqual(7, program.cooling_relay_index)
        self.assertEqual(17.5, program.min_temperature)
        self.assertEqual(18.4, program.max_temperature)
        self.assertEqual(True, program.active)

        json_data = {"id": PROGRAM_ID,
                     "name": "program2",
                     "crc": "crc2",
                     "sensor_id": "1003",
                     "heating_relay_index": -1,
                     "cooling_relay_index": -1,
                     "min_temp": 17.2,
                     "max_temp": 18.3,
                     "active": False}
        json_str = json.dumps(json_data)
        program = Program.from_json(json_str)
        self.assertEqual(PROGRAM_ID, program.program_id)
        self.assertEqual("program2", program.program_name)
        self.assertEqual("1003", program.sensor_id)
        self.assertEqual(-1, program.heating_relay_index)
        self.assertEqual(-1, program.cooling_relay_index)
        self.assertEqual(17.2, program.min_temperature)
        self.assertEqual(18.3, program.max_temperature)
        self.assertEqual(False, program.active)

    def test_modify_with_program(self):
        program1 = Program(program_id="id1", program_name="name1", sensor_id="sensor1",
                                  heating_relay_index=1, cooling_relay_index=2,
                                  min_temperature=15.0, max_temperature=17.0, active=True)
        program2 = Program(program_id="id2", program_name="name2", sensor_id="sensor2",
                                  heating_relay_index=3, cooling_relay_index=4,
                                  min_temperature=15.1, max_temperature=17.1, active=True)

        # create modified program using values of other program
        modified = program1.modify_with(program2)
        self.assertEqual(program1.program_id, modified.program_id)
        self.assertEqual(program2.program_name, modified.program_name)
        self.assertEqual(program2.sensor_id, modified.sensor_id)
        self.assertEqual(program2.heating_relay_index, modified.heating_relay_index)
        self.assertEqual(program2.cooling_relay_index, modified.cooling_relay_index)
        self.assertEqual(program2.min_temperature, modified.min_temperature)
        self.assertEqual(program2.max_temperature, modified.max_temperature)
        self.assertEqual(program2.active, modified.active)

        # create modified program using values of itself and some given extra values
        modified = program1.modify_with(program1, program_name="extra_name")
        self.assertEqual(program1.program_id, modified.program_id)
        self.assertEqual("extra_name", modified.program_name)
        self.assertEqual(program1.sensor_id, modified.sensor_id)
        self.assertEqual(program1.heating_relay_index, modified.heating_relay_index)
        self.assertEqual(program1.cooling_relay_index, modified.cooling_relay_index)
        self.assertEqual(program1.min_temperature, modified.min_temperature)
        self.assertEqual(program1.max_temperature, modified.max_temperature)
        self.assertEqual(program1.active, modified.active)

        # create modified program using values of itself and some given extra values (all values)
        modified = program1.modify_with(program1, program_name="extra_name", sensor_id="extra_sensor",
                                        heating_relay_index="extra_heat", cooling_relay_index="extra_cool",
                                        min_temperature=10.0, max_temperature=11.0, active=False)
        self.assertEqual(program1.program_id, modified.program_id)
        self.assertEqual("extra_name", modified.program_name)
        self.assertEqual("extra_sensor", modified.sensor_id)
        self.assertEqual("extra_heat", modified.heating_relay_index)
        self.assertEqual("extra_cool", modified.cooling_relay_index)
        self.assertEqual(10.0, modified.min_temperature)
        self.assertEqual(11.0, modified.max_temperature)
        self.assertEqual(False, modified.active)
