import requests
import paramiko
import json
import os


class TPMService:
    """
    A class that provides methods for interacting with a TPM service.
    """

    def __init__(self, config):
        """
        Initializes the TPMService object.

        Args:
            config (dict): A dictionary containing the configuration parameters.
                - local_records (bool): Flag indicating whether to use local records or not.
                - local_records_dir (str): Path to the local records directory.
                - ssh_key (str): Path to the SSH private key file.
                - password (str): Password for the SSH private key.
                - address (str): Address of the TPM service.
                - username (str): Username for the SSH connection.
                - pid_enpoint (str): Endpoint for retrieving records by PID.
        """
        self.local_records = config["local_records"]
        if self.local_records:
            filename = config["local_records_dir"]
            wd = os.getcwd()
            combined_path = os.path.join(wd, filename)
            self.local_records_dir = os.path.abspath(combined_path)
        else:
            ssh_key = paramiko.RSAKey.from_private_key_file(config["ssh_key"], password=config["password"])
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(config["address"], username=config["username"], pkey=ssh_key)
            self.pid_enpoint = config["pid_enpoint"]
            self.ssh_client.invoke_shell()

    def close_connection(self):
        """
        Closes the SSH connection.
        """
        self.ssh_client.close()

    def is_dict_string(self, s):
        """
        Checks if a string is a valid JSON dictionary.

        Args:
            s (str): The string to check.

        Returns:
            bool: True if the string is a valid JSON dictionary, False otherwise.
        """
        return isinstance(s, str) and s.startswith('{') and s.endswith('}')

    def convert_string_to_dict(self, data):
        """
        Recursively converts string values in a dictionary to their corresponding Python objects.

        Args:
            data (dict or list): The dictionary or list to convert.

        Returns:
            dict or list: The converted dictionary or list.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    try:
                        data[key] = eval(value)
                    except (SyntaxError, NameError):
                        pass
                elif isinstance(value, (list, dict)):
                    self.convert_string_to_dict(value)
        elif isinstance(data, list):
            for i in range(len(data)):
                if isinstance(data[i], dict):
                    self.convert_string_to_dict(data[i])
        return data

    def get_record(self, pid):
        """
        Retrieves a record by PID.

        Args:
            pid (str): The PID of the record to retrieve.

        Returns:
            dict or None: The record as a dictionary if found, None otherwise.
        """
        if self.local_records is False:
            url = self.pid_enpoint + pid
            headers = {
                "accept": "application/json"
            }
            response = requests.get(url, headers=headers)
            json_response = response.json()
            return json_response
        else:
            try:
                with open(self.local_records_dir, 'r') as file:
                    pid_dict = json.load(file)
            except FileNotFoundError:
                print(f"The file {self.local_records_dir} was not found.")
            except json.JSONDecodeError:
                print(f"Error decoding JSON from the file {self.local_records_dir}.")
            try:
                pid_dict[pid]["entries"] = self.convert_string_to_dict(pid_dict[pid]["entries"])
                return pid_dict[pid]
            except KeyError:
                return None