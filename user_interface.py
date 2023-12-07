from flask import Flask, render_template, request, redirect, session
import os
import json
from redis import Redis
import requests
import ast
from modules.sparql_service import SPARQLService
from modules.tpm_service import TPMService
from modules.record_mapper import RecordMapper
from modules.kernel_workflow import KernelWorkflow
from modules.query_processing import QueryProcessing
from modules.ops_executor import Ops_Executor

app = Flask(__name__)
redis_client = Redis(host='localhost', port=6379, db=0, decode_responses=True)

current_dir = os.path.dirname(__file__)
services_config = os.path.join(current_dir, "configs/services.json")
tpm_keys_config_path = os.path.join(current_dir, "configs/tpm_keys_config_path.json")
validation_config_path = os.path.join(current_dir, "configs/validation_config_path.json")

with open(services_config, 'r') as services_config_file:
    services_config_file = json.load(services_config_file)

app.secret_key = os.environ.get('SECRET_KEY', 'default-secret-key-for-development-only')  # you should set SECRET_KEY environment variable in production

sparql_service = SPARQLService(services_config_file["graph_db"])
tpm_service = TPMService(services_config_file["tpm"])
executor = Ops_Executor()
query_processing = QueryProcessing()
validator = KernelWorkflow(tpm_keys_config_path)
mapper = RecordMapper(tpm_keys_config_path)


def get_operations_for_profile(profile, data):
    """
    Get operations for the given profile.

    :param profile: The profile to get operations for.
    :param data: The data containing the profiles and operations.
    :return: A dictionary of operations for the given profile.
    """
    # Get data for the given profile
    profile_data = data.get(profile, {})

    # Organize operations and their digital objects
    operations = {}
    for operation, operation_output_fdos in profile_data.items():
        if operation not in operations:
            operations[operation] = []
            for operation_output, fdo in profile_data.items():
                operations[operation].extend(fdo)

    return operations


def get_local_path(folder_name):
    """
    Check if a folder with the given name exists in the specified directory.

    :param folder_name: The name of the folder to check.
    :return: Full path to the folder if it exists, None otherwise.
    """
    # Define the static directory (relative path)
    directory = "."

    # Get the absolute path of the directory
    dir_path = os.path.abspath(directory)

    # Check if the directory exists
    if not os.path.exists(dir_path):
        print(f"Directory {directory} does not exist.")
        return None

    # Iterate through the items in the directory
    for item in os.listdir(dir_path):
        item_path = os.path.join(dir_path, item)
        # Check if the item is a directory and matches the folder name
        if os.path.isdir(item_path) and item == folder_name:
            return item_path

    return None


def convert_to_dict(lst):
    """
    Convert a list of strings to a dictionary.

    :param lst: The list of strings to convert.
    :return: The converted dictionary.
    """
    result_dict = {}
    for item in lst:
        parts = item.split('|')
        try:
            # Convert the string representation of the list to an actual list
            fdos = ast.literal_eval(parts[2])
            ops = parts[0]
            outputType = parts[1]
            result_dict[ops] = (outputType, fdos)
        except ValueError:
            localPath = [get_local_path(parts[0])]  # enable also for multiple directions in case multiple inputs are required.
            ops = parts[1]
            outputType = parts[2]
            result_dict[ops] = (outputType, localPath)
    return result_dict


@app.route('/execute_query', methods=['GET', 'POST'])
def execute_query():
    """
    Execute the SPARQL query.

    :return: The rendered template or a redirect.
    """
    if request.method == 'POST':
        query_type = request.form.get('query_select')
        input_text = request.form.get('input_text')

        if query_type == 'profiles':
            # Construct the SPARQL query for Query 1
            sparql_query = sparql_service.construct_query1(input_text)
        elif query_type == 'attributes':
            # Construct the SPARQL query for Query 2
            sparql_query = sparql_service.construct_query2(input_text)

        # Execute SPARQL query and get PIDs
        results = sparql_service.execute_query(sparql_query)
        structured_data = query_processing.restructure_query_result(results)
        redis_client.set('restructured_results', json.dumps(structured_data))

        if query_type == 'profiles':
            return redirect('/select_profiles')
        else:
            return redirect('/select_attributes')

    # For GET request, display the form for SPARQL query submission
    return render_template('submit_sparql.html')


@app.route('/select_profiles', methods=['GET', 'POST'])
def select_profiles():
    """
    Select profiles.

    :return: The rendered template or a redirect.
    """
    if request.method == 'POST':
        selected_profiles = request.form.getlist('selected_items')
        redis_client.set('selection', json.dumps(selected_profiles))
        session['sparql_query'] = "profiles"
        return redirect('/get_pids')

    # For GET request, display the hierarchical data to the user
    data = json.loads(redis_client.get('restructured_results'))
    return render_template('select_profiles.html', data=data)


@app.route('/select_attributes', methods=['GET', 'POST'])
def select_attributes():
    """
    Select attributes.

    :return: The rendered template or a redirect.
    """
    if request.method == 'POST':
        selected_attributes = request.form.getlist('selected_items')
        redis_client.set('selection', json.dumps(selected_attributes))
        session['sparql_query'] = "attributes"
        return redirect('/get_pids')

    # For GET request, display the hierarchical data to the user
    data = json.loads(redis_client.get('restructured_results'))
    return render_template('select_attributes.html', data=data)

def timeout_handler(self, signum, frame):
        raise TimeoutError

@app.route('/get_pids', methods=['GET', 'POST'])
def get_pids():
    """
    Get PIDs.

    :return: The rendered template.
    """
    sparql_query = session.get('sparql_query', {})
    selected_pids = json.loads(redis_client.get('selection'))
    data = convert_to_dict(selected_pids)
    responses = []
    for op, tuple_ in data.items():
        op_record = tpm_service.get_record(op)
        is_valid_op = validator.validate(op_record, checksum=False)
        if not is_valid_op:
            # Handle invalid digital object
            continue
        outputType = tuple_[0]
        if sparql_query == "profiles":
            for fdo in tuple_[1]:
                fdo_record = tpm_service.get_record(fdo)
                if fdo == "21.11152/02652ab1-58e4-409f-bcff-c2194bf345b8":
                    continue
                is_valid_data = validator.validate(fdo_record)
                print(is_valid_data)
                if not is_valid_data:
                    print("not valid:",fdo)
                    # Handle invalid digital object
                    continue
                returned_requests = mapper.map_to_request(op_record["entries"], fdo_record["entries"], local_access=False)
                if list(returned_requests.keys())[0] == "http":
                    for req in list(returned_requests.values())[0]:
                        response, folder_name = executor.execute_http_request(fdo, req, outputType)
                        if response == "Request failed":
                            pass
                        else:
                            responses.append(response)
        elif sparql_query == "attributes":
            local_dir = tuple_[1][0]  # currently only one level of input attributes
            for file in os.listdir(local_dir):
                filepath = os.path.join(local_dir, file)
                filename, _ = os.path.splitext(file)
                returned_requests = mapper.map_to_request(op_record["entries"], None, True, filepath)
                if list(returned_requests.keys())[0] == "http":
                    for req in list(returned_requests.values())[0]:
                        response, folder_name = executor.execute_http_request(filename, req, outputType)
                        if response == "Request failed":
                            pass
                        else:
                            responses.append(response)

    return render_template('display_response.html', outputType=outputType, folder_name=folder_name, responses=responses)


@app.route('/end_session', methods=['GET'])
def end_session():
    """
    End the session.

    :return: A redirect.
    """
    session.pop('mapped_requests', None)
    return redirect('/execute_query')


@app.route('/')
def index():
    """
    Redirect to the execute_query route.

    :return: A redirect.
    """
    return redirect('/execute_query')


if __name__ == '__main__':
    app.run(port=5004, debug=True)