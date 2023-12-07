import json
from datetime import datetime, timedelta
import hashlib
import requests


class KernelWorkflow:
    def __init__(self, tpm_keys_config_path, tpm_service=None):
        """
        Initializes the KernelWorkflow class.

        Args:
        - tpm_keys_config_path (str): The path to the TPM keys configuration file.
        - tpm_service (optional): The TPM service to use.
        """
        with open(tpm_keys_config_path, 'r') as file:
            self.tpm_keys = json.load(file)

    def validate(self, record, checksum=True):
        """
        Validates the given record against the predefined key-value pairs in the configuration.
        Also resolves specific keys using the TPM.

        Args:
        - record (dict): The JSON record to validate.
        - checksum (bool, optional): Whether to perform checksum evaluation. Default is True.

        Returns:
        - bool: True if the record is valid, False otherwise.
        """
        
        if record is None:
            return False
        try:
            result = self.check_url(record["entries"][self.tpm_keys["digitalObjectLocation"]])
            if result is False:
                return False
            result = self.date_evaluation(record["entries"][self.tpm_keys["dateCreated"]])
            if result is False:
                return False
            if checksum is True:
                result = self.checksum_evaluation(record["entries"][self.tpm_keys["digitalObjectLocation"]], record["entries"][self.tpm_keys["checksum"]])
                if result is False:
                    return False
            result = self.license_evaluation(record["entries"][self.tpm_keys["license"]])
            if result is False:
                return False
        except KeyError as e:
            return False
        return True

    def check_url(self, url):
        """
        Checks if the given URL(s) are valid.

        Args:
        - url (str or list): The URL(s) to check.

        Returns:
        - bool or list: True if at least one URL is valid, False otherwise.
        """
        valid_urls = []
        for url in url:
            try:
                response = requests.head(url["value"], timeout=5)
                if response.status_code // 100 in {2, 3}:
                    valid_urls.append(url)
                elif response.status_code == 405:  # only for validating an operation's availability
                    valid_urls.append(url)
                elif response.status_code == 404:  # only for validating an operation's availability
                    valid_urls.append(url)
            except requests.RequestException:
                pass
        if len(valid_urls) > 0:
            return valid_urls
        else:
            return False

    def date_evaluation(self, date):
        """
        Evaluates if the given date is up to date.

        Args:
        - date (str): The date to evaluate.

        Returns:
        - bool: True if the date is is up to date, False otherwise.
        """
        date = datetime.strptime(date[0]["value"], "%Y-%m-%dT%H:%M:%S%z")
        now = datetime.now(date.tzinfo)
        border = now - timedelta(days=55*365.25)
        return date > border

    def license_evaluation(self, license):
        """
        Evaluates if the given license is an open source license.

        Args:
        - license (str): The license to evaluate.

        Returns:
        - bool: True if the license is an open source license, False otherwise.
        """
        open_source_licenses = [
            'https://creativecommons.org/licenses/by/4.0/',
            'MIT License',
            'GNU General Public License v3.0',
            'Apache License 2.0',
            'BSD 2-Clause "Simplified" License',
            'BSD 3-Clause "New" or "Revised" License',
            'https://creativecommons.org/publicdomain/zero/1.0',
            'https://creativecommons.org/licenses/by/3.0/',
            'http://creativecommons.org/licenses/by-sa/3.0/igo/',
            'https://creativecommons.org/licenses/by-nc-sa/4.0/'
        ]
        return license[0]["value"] in open_source_licenses

    def checksum_evaluation(self, urls, checksums):
        """
        Evaluates if the checksums of the given URLs match the provided checksums.

        Args:
        - urls (list): The URLs to evaluate.
        - checksums (dict): The checksums to compare against.

        Returns:
        - bool: True if at least one checksum does not match, False otherwise.
        """
        responses = []
        checksums = checksums[0]["value"]

        for url in urls:
            response = requests.get(url["value"])
            document_content = response.text

            for key, value in checksums.items():
                if key == "sha256sum":
                    calc_checksum = hashlib.sha256(document_content.encode()).hexdigest()
                    responses.append('\"'+value+'\"' != calc_checksum)
                elif key == "sha512sum":
                    calc_checksum = hashlib.sha512(document_content.encode()).hexdigest()
                    responses.append('\"'+value+'\"' != calc_checksum)
                elif key == "md5sum":
                    calc_checksum = hashlib.md5(document_content.encode()).hexdigest()
                    responses.append('\"'+value+'\"' != calc_checksum)
        if True in responses:
            return True
        else:
            return False