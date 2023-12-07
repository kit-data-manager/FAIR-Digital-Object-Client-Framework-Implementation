import os
import requests
import unittest
from unittest.mock import patch
from tempfile import TemporaryDirectory

from modules.ops_executor import Ops_Executor


class TestOpsExecutor(unittest.TestCase):
    def setUp(self):
        self.executor = Ops_Executor()

    def test_execute_http_request_success(self):
        with TemporaryDirectory() as temp_dir:
            file_name = "test_file"
            request_string = 'requests.get("https://example.com")'
            folder_name = temp_dir

            status, folder = self.executor.execute_http_request(file_name, request_string, folder_name)

            self.assertEqual(status, "Request successful")
            self.assertEqual(folder, folder_name)

            # Check if the file was created
            self.assertTrue(os.path.exists(os.path.join(folder_name, file_name)))

    def test_execute_http_request_failure(self):
        with TemporaryDirectory() as temp_dir:
            file_name = "test_file"
            request_string = 'requests.get("https://nonexistent-url.com")'
            folder_name = temp_dir

            status, folder = self.executor.execute_http_request(file_name, request_string, folder_name)

            self.assertEqual(status, "Request failed")
            self.assertEqual(folder, folder_name)

    def test_execute_http_request_with_content_disposition(self):
        with TemporaryDirectory() as temp_dir:
            file_name = "test_file"
            request_string = 'requests.get("https://example.com")'
            folder_name = temp_dir

            # Mock the response headers
            headers = {'Content-Disposition': 'attachment; filename="example.txt"'}
            with patch('requests.get') as mock_get:
                mock_get.return_value.status_code = 200
                mock_get.return_value.headers = headers
                mock_get.return_value.content = b'Test content'

                status, folder = self.executor.execute_http_request(file_name, request_string, folder_name)

                self.assertEqual(status, "Request successful")
                self.assertEqual(folder, folder_name)

                # Check if the file was created with the correct name
                self.assertTrue(os.path.exists(os.path.join(folder_name, file_name + "_example.txt")))

    def test_execute_http_request_with_content_type(self):
        with TemporaryDirectory() as temp_dir:
            file_name = "test_file"
            request_string = 'requests.get("https://example.com")'
            folder_name = temp_dir

            # Mock the response headers
            headers = {'Content-Type': 'application/json'}
            with patch('requests.get') as mock_get:
                mock_get.return_value.status_code = 200
                mock_get.return_value.headers = headers
                mock_get.return_value.content = b'Test content'

                status, folder = self.executor.execute_http_request(file_name, request_string, folder_name)

                self.assertEqual(status, "Request successful")
                self.assertEqual(folder, folder_name)

                # Check if the file was created with the correct extension
                self.assertTrue(os.path.exists(os.path.join(folder_name, file_name + ".json")))


if __name__ == '__main__':
    unittest.main()