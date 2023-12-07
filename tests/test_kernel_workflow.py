import unittest
from datetime import datetime, timedelta
import hashlib
import requests
from unittest.mock import patch, MagicMock

from modules.kernel_workflow import KernelWorkflow

class TestKernelWorkflow(unittest.TestCase):

    def setUp(self):
        self.workflow = KernelWorkflow("configs/tpm_keys_config_path.json")

    def test_validate_valid_record(self):
        record = {
            "entries": {
                "digitalObjectLocation": "https://example.com",
                "dateCreated": "2022-01-01T00:00:00+00:00",
                "checksum": "abc123",
                "license": "MIT License"
            }
        }
        result = self.workflow.validate(record)
        self.assertTrue(result)

    def test_validate_invalid_record(self):
        record = {
            "entries": {
                "digitalObjectLocation": "https://example.com",
                "dateCreated": "2000-01-01T00:00:00+00:00",
                "checksum": "abc123",
                "license": "Invalid License"
            }
        }
        result = self.workflow.validate(record)
        self.assertFalse(result)

    def test_check_url_valid(self):
        url = "https://example.com"
        with patch('requests.head') as mock_head:
            mock_head.return_value.status_code = 200
            result = self.workflow.check_url(url)
            self.assertEqual(result, [url])

    def test_check_url_invalid(self):
        url = "https://example.com"
        with patch('requests.head') as mock_head:
            mock_head.return_value.status_code = 404
            result = self.workflow.check_url(url)
            self.assertFalse(result)

    def test_date_evaluation_within(self):
        date = "2022-01-01T00:00:00+00:00"
        result = self.workflow.date_evaluation(date)
        self.assertTrue(result)

    def test_date_evaluation_not_within(self):
        date = "1950-01-01T00:00:00+00:00"
        result = self.workflow.date_evaluation(date)
        self.assertFalse(result)

    def test_license_evaluation_valid(self):
        license = "MIT License"
        result = self.workflow.license_evaluation(license)
        self.assertTrue(result)

    def test_license_evaluation_invalid(self):
        license = "Invalid License"
        result = self.workflow.license_evaluation(license)
        self.assertFalse(result)

    def test_checksum_evaluation_matching_checksums(self):
        urls = ["https://example.com"]
        checksums = {"sha256sum": "abc123"}
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = "example content"
            mock_get.return_value = mock_response
            result = self.workflow.checksum_evaluation(urls, checksums)
            self.assertFalse(result)

    def test_checksum_evaluation_not_matching_checksums(self):
        urls = ["https://example.com"]
        checksums = {"sha256sum": "invalid_checksum"}
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = "example content"
            mock_get.return_value = mock_response
            result = self.workflow.checksum_evaluation(urls, checksums)
            self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
