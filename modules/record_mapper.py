import json
import ast
import os
class RecordMapper:
    def __init__(self, tpm_keys_config_path):
        """
        Initialize the RecordMapper class.

        Args:
            tpm_keys_config_path (str): The path to the TPM keys configuration file.
        """
        with open(tpm_keys_config_path, 'r') as file:
            self.tpm_keys = json.load(file)

    def parse_json_like_string(self, record):
        """
        Parse a JSON-like string in a record and convert it into a dictionary.

        Args:
            record (dict): The record containing the JSON-like string.

        Returns:
            dict: The record with the parsed JSON-like string.
        """
        for key, value_list in record["entries"].items():
            for item in value_list:
                if isinstance(item["value"], str) and item["value"].startswith("{"):
                    json_like_str = item["value"].replace("'", '"')
                    # Handle other specific formatting issues here if necessary

                    # Parse the string into a dictionary
                    try:
                        item["value"] = json.loads(json_like_str)
                    except json.JSONDecodeError:
                        # Fallback to ast.literal_eval if json.loads fails
                        try:
                            item["value"] = ast.literal_eval(json_like_str)
                        except ValueError:
                            pass
        return record["entries"]

    def map_to_request(self, operation_record: str, data_record: str, local_access: bool, local_file_path: str=None):
        """
        Map an operation record and a data record to a request.

        Args:
            operation_record (str): The operation record.
            data_record (str): The data record.
            local_access (bool): Flag indicating if local access is enabled.
            local_file_path (str, optional): The local file path. Defaults to None.

        Returns:
            dict: The mapped requests.
        """
        if local_access is True:
            access_protocol = operation_record[self.tpm_keys["localPathAccessProtocol"]][0]["value"][self.tpm_keys["operationAccessProtocol"]]
        else:
            access_protocol = operation_record[self.tpm_keys["externalRecordDependentAccessProtocol"]][0]["value"][self.tpm_keys["operationAccessProtocol"]]
        ops_location = operation_record[self.tpm_keys["digitalObjectLocation"]][0]["value"]
        mapped_requests = {}

        for protocol in access_protocol:
            if self.tpm_keys["httpProtocol"] in protocol["value"]:
                mapped_requests["http"] = self.map_http_record(protocol["value"][self.tpm_keys["httpProtocol"]][0]["value"], data_record, ops_location, local_file_path)
            # Add other mappings here

        return mapped_requests

    def map_http_record(self, operation_record, data_record, ops_location, local_file_path):
        """
        Map an HTTP operation record to a request.

        Args:
            operation_record (dict): The HTTP operation record.
            data_record (str): The data record.
            ops_location (str): The operation location.
            local_file_path (str): The local file path.

        Returns:
            list: The mapped requests.
        """
        mapped_requests = []
        executable = "requests." + str(operation_record[self.tpm_keys["httpMethod"]][0]["value"]).lower() + "('" + str(ops_location) + "'"

        if (self.tpm_keys["httpParameter"] in operation_record) and (data_record is not None):
            payloads = []
            payloads_temp = []
            for i in operation_record[self.tpm_keys["httpParameter"]]:
                for j in data_record[i["value"][self.tpm_keys["parameterValueType"]][0]["value"]]:
                    if len(payloads) > 1:
                        for z in payloads_temp:
                            z[i["value"][self.tpm_keys["parameterKey"]][0]["value"]] = j["value"]
                    else:
                        payload = {}
                        payload[i["value"][self.tpm_keys["parameterKey"]][0]["value"]] = j["value"]
                        payloads_temp.append(payload)
                payloads = payloads_temp
            for x in payloads:
                executable_temp = executable + ", params=" + str(x) + ")"
                mapped_requests.append(executable_temp)

        if self.tpm_keys["httpHeaderProperty"] in operation_record:
            headers = {}
            for i in operation_record[self.tpm_keys["httpHeaderProperty"]]:
                headers[str(i["value"][self.tpm_keys["headerKey"]][0]["value"])] = str(i["value"][self.tpm_keys["headerValue"]][0]["value"])
            if len(mapped_requests) > 0:
                executable_temp = ", headers=" + str(headers) + ")"
                mapped_requests_temp = []
                for y in mapped_requests:
                    mapped_requests_temp.append(y + executable_temp)
                mapped_requests = mapped_requests_temp
            else:
                executable_temp = executable + ", headers=" + str(headers) + ")"
                mapped_requests.append(executable_temp)

        if (self.tpm_keys["httpDataProperty"] in operation_record) and (data_record is not None):
            datas = []
            datas_temp = []
            for i in operation_record[self.tpm_keys["httpDataProperty"]]:
                for j in data_record[i["value"][self.tpm_keys["dataValueType"]][0]["value"]]:
                    if len(datas) >= 1:
                        for z in datas_temp:
                            z[i["value"][self.tpm_keys["dataKey"]][0]["value"]] = j["value"]
                    else:
                        data = {}
                        data[i["value"][self.tpm_keys["dataKey"]][0]["value"]] = j["value"]
                        datas_temp.append(data)
                datas = datas_temp
            if len(mapped_requests) > 0:
                mapped_requests_temp = []
                for x in datas:
                    executable_temp = ", data=" + str(x) + ")"
                    for y in mapped_requests:
                        mapped_requests_temp.append(y + executable_temp)
                mapped_requests = mapped_requests_temp
            else:
                for x in datas:
                    executable_temp = executable + ", data=" + str(x) + ")"
                    mapped_requests.append(executable_temp)

        if self.tpm_keys["httpMultipartFormDataProperty"] in operation_record:
            files = {}
            print(local_file_path)
            for i in operation_record[self.tpm_keys["httpMultipartFormDataProperty"]]:
                _, file_extension = os.path.splitext(local_file_path)
                if "txt" in file_extension:
                    files[i["value"][self.tpm_keys["fileKey"]][0]["value"]] = f'open("{local_file_path}", "r")'
                else:
                    files[i["value"][self.tpm_keys["fileKey"]][0]["value"]] = f'open("{local_file_path}", "rb")'
            if len(mapped_requests) > 0:
                executable_temp = f", files={files}"
                mapped_requests_temp = []
                for y in mapped_requests:
                    mapped_requests_temp.append(y + executable_temp)
                mapped_requests = mapped_requests_temp
            else:
                executable_temp = executable + ", files=" + str(files) + ")"
                mapped_requests.append(executable_temp)

        return mapped_requests
