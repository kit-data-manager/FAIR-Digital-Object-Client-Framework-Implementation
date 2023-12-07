

import unittest
from unittest.mock import mock_open, patch
from modules.record_mapper import RecordMapper

class TestRecordMapper(unittest.TestCase):

    def test_parse_json_like_string(self):
        record = {
            "entries": {
                "key1": [
                    {"value": "{'name': 'John', 'age': 30}"}
                ],
                "key2": [
                    {"value": "{'name': 'Jane', 'age': 25}"}
                ]
            }
        }
        expected_result = {
            "key1": [
                {"value": {"name": "John", "age": 30}}
            ],
            "key2": [
                {"value": {"name": "Jane", "age": 25}}
            ]
        }
        mapper = RecordMapper("tpm_keys_config.json")
        result = mapper.parse_json_like_string(record)
        self.assertEqual(result, expected_result)

    def test_map_to_request_local_access(self):
        operation_record = {
            "localPathAccessProtocol": [
                {"value": {
                    "operationAccessProtocol": "http"
                }}
            ],
            "digitalObjectLocation": [
                {"value": "http://example.com"}
            ]
        }
        data_record = "some data"
        local_access = True
        local_file_path = "/path/to/file.txt"
        expected_result = {
            "http": [
                "requests.get('http://example.com', params={}, headers={}, files={})"
            ]
        }
        mapper = RecordMapper("tpm_keys_config.json")
        result = mapper.map_to_request(operation_record, data_record, local_access, local_file_path)
        self.assertEqual(result, expected_result)

    # Add more tests here

if __name__ == "__main__":
    unittest.main()

