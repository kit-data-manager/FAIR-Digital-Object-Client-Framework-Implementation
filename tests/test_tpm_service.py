import unittest
from unittest.mock import patch, MagicMock
from modules.tpm_service import TPMService

class TestTPMService(unittest.TestCase):

    def setUp(self):
        self.config = {
            "local_records": True,
            "local_records_dir": "/path/to/local/records",
            "ssh_key": "/path/to/ssh/key",
            "password": "password",
            "address": "tpm-service-address",
            "username": "username",
            "pid_enpoint": "pid-endpoint"
        }
        self.tpm_service = TPMService(self.config)

    def tearDown(self):
        self.tpm_service.close_connection()

    def test_is_dict_string(self):
        self.assertTrue(self.tpm_service.is_dict_string('{"key": "value"}'))
        self.assertFalse(self.tpm_service.is_dict_string('[1, 2, 3]'))
        self.assertFalse(self.tpm_service.is_dict_string('not a dictionary'))

    def test_convert_string_to_dict(self):
        data = {
            "key1": "value1",
            "key2": "value2",
            "key3": "[1, 2, 3]"
        }
        converted_data = self.tpm_service.convert_string_to_dict(data)
        self.assertEqual(converted_data["key1"], "value1")
        self.assertEqual(converted_data["key2"], "value2")
        self.assertEqual(converted_data["key3"], [1, 2, 3])

    @patch('requests.get')
    def test_get_record_remote(self, mock_get):
        pid = "12345"
        expected_response = {
            "pid": pid,
            "entries": {
                "key1": "value1",
                "key2": "value2"
            }
        }
        mock_get.return_value.json.return_value = expected_response
        record = self.tpm_service.get_record(pid)
        self.assertEqual(record, expected_response)

    @patch('builtins.open', new_callable=MagicMock)
    def test_get_record_local(self, mock_open):
        pid = "12345"
        expected_response = {
            "pid": pid,
            "entries": {
                "key1": "value1",
                "key2": "value2"
            }
        }
        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_file.read.return_value = '{"12345": {"entries": {"key1": "value1", "key2": "value2"}}}'
        mock_open.return_value = mock_file
        record = self.tpm_service.get_record(pid)
        self.assertEqual(record, expected_response)

if __name__ == '__main__':
    unittest.main()

