from flask import Flask, request, jsonify, Response
import requests
import skosify
import io
import logging
import json
from tempfile import NamedTemporaryFile
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
# Configure logging to capture output
log_capture = io.StringIO()
logging.basicConfig(stream=log_capture, level=logging.INFO)


def get_total_term_count(base_url: str, vocabulary_id: str) -> int:
    """
    Returns the number of total terms in a vocabulary.

    Args:
        base_url (str): The base URL of the API.
        vocabulary_id (str): The ID of the vocabulary.

    Returns:
        int: The total count of terms in the vocabulary.
    """
    count_slug = "vocabularyStatistics"
    api_url = f"{base_url}/{vocabulary_id}/{count_slug}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Check for any request errors

        json_data = response.json()

        # Extracting the total count from the 'concepts' section
        total_count = json_data.get("concepts", {}).get("count")
        if total_count is not None:
            print(f"The total 'count' value from '{base_url}' is: {total_count} terms")
        else:
            print("Failed to retrieve the total 'count' value from the API.")
        return total_count

    except requests.RequestException as e:
        print(f"Request error: {e}")
        return None


def download_rdf_content(base_url: str, vocabulary_id: str) -> tuple:
    """
    Downloads the vocabulary in RDF/XML or turtle format.

    Args:
        base_url (str): The base URL of the API.
        vocabulary_id (str): The ID of the vocabulary.

    Returns:
        tuple: The content of the vocabulary and its MIME type if successful, else (None, None).
    """
    mime_types = {
        'rdfxml': 'application/rdf+xml',
        'turtle': 'text/turtle'
    }
    api_url = f"{base_url}{vocabulary_id}/data?format={}"
    for mime_type in ['rdfxml', 'turtle']:
        try:
            response = requests.get(api_url.format(mime_types[mime_type]))
            response.raise_for_status()

            if response.content:
                return response.content, mime_types[mime_type]

        except requests.HTTPError as e:
            print(f"Error with MIME type '{mime_types[mime_type]}': {e}")
    return None, None


def convert_to_skos_rdfxml(file_name: str) -> str:
    """
    Converts a turtle file to SKOS RDF/XML format.

    Args:
        file_name (str): The name of the turtle file.

    Returns:
        str: The converted content in RDF/XML format if successful, else None.
    """
    try:
        # Convert the input file to SKOS RDF/XML format
        voc = skosify.skosify(file_name)
        rdf_xml_content = voc.serialize(format='xml')
        return rdf_xml_content

    except Exception as e:
        print(f"Conversion failed: {e}")
        return jsonify({"error": "Failed to convert from turtle to rdf/xml"}), 400


def skos_rdf_validate(file_name: str) -> str:
    """
    Validates if a file is well-formed SKOS RDF/XML.

    Args:
        file_name (str): The name of the RDF/XML file.

    Returns:
        str: The validation output if successful, else None.
    """
    try:
        log_capture.truncate(0)  # Clear the existing captured logs
        # Convert the input file to SKOS RDF/XML format
        voc = skosify.skosify(file_name)
        voc.serialize(destination="/dev/null", format='xml')
        output = log_capture.getvalue()  # Retrieve the captured logs from skosify
        print("Validation successfully performed")
        return output
    except SystemExit as systemexit:
        if systemexit.code == 1:
            # Do something if 'test' exits with sys.exit(1)
            print("Validation failed")
            jsonify({"Verification failed"}), 400
    except Exception as e:
        print(f"Validation failed: {e}")
        jsonify({"Verification failed"}), 400


def search_skohub(vocabulary_domain: str) -> str:
    """
    Returns the language(s) of a vocabulary.

    Args:
        vocabulary_domain (str): The domain of the vocabulary.

    Returns:
        str: The language(s) of the vocabulary if provided, else None.
    """
    try:
        response = requests.get(vocabulary_domain)
        response.raise_for_status()  # Check for any request errors

        json_data = response.json()
        # Extracting the total count from the 'concepts' section
        domain_label = json_data.get("prefLabel")
        if domain_label is not None:
            print(f"All supported languages from '{vocabulary_domain}' are: {domain_label}")
        else:
            print("Failed to retrieve the languages from the API.")
        return domain_label

    except requests.RequestException as e:
        print(f"Request error: {e}")
        return None


# API endpoint to get all languages
@app.route('/get_domain', methods=['POST'])
def get_domain():
    vocabulary_domain = request.form.get('vocabulary_domain')

    vocabulary_domains = search_skohub(vocabulary_domain)
    print(vocabulary_domains)
    vocabs_json = json.dumps(vocabulary_domains)

    if vocabulary_domains:
        response = Response(vocabs_json, status=200, mimetype='application/json')
        response.headers['Message'] = 'Successfully retrieved domains.'
        response.headers['Content-Disposition'] = 'attachment; filename="domains.json"'
        return response
    else:
        return jsonify({"error": "Failed to retrieve domains."}), 400


@app.route('/convert_turtle_to_rdfxml', methods=['POST'])
def convert_turtle():
    uploaded_file = request.files['vocabulary_id']

    if uploaded_file:
        filename = secure_filename(uploaded_file.filename)
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext in ['.rdf', '.xml', '.n3']:
            return jsonify({"message": "No ttl file uploaded"}), 400
        # Create a temporary file to save the uploaded file
        with NamedTemporaryFile(delete=False, suffix='.ttl') as temp_file:
            uploaded_file.save(temp_file)
            temp_file_path = temp_file.name

        try:
            # Now pass this temporary file path to the conversion function
            rdf_xml_content = convert_to_skos_rdfxml(temp_file_path)

            # After conversion, remove the temporary file
            os.remove(temp_file_path)

            if rdf_xml_content:
                response = Response(rdf_xml_content, status=200, mimetype='application/rdf+xml')
                response.headers['Content-Disposition'] = f'attachment; filename={uploaded_file.filename}.rdf'
                response.headers['Message'] = 'Vocabulary successfully converted.'
                return response
            else:
                return jsonify({"message": "Failed to convert from turtle to rdf/xml"}), 400

        except Exception as e:
            # Remove the temporary file in case of an exception
            os.remove(temp_file_path)
            return jsonify({"error": str(e)}), 500

    return jsonify({"message": "No file uploaded"}), 400


@app.route('/total_term_count', methods=['POST'])
def total_term_count():
    base_url = request.form.get('base_url')
    vocabulary_id = request.form.get('vocabulary_id')

    if base_url and vocabulary_id:
        total_count = get_total_term_count(base_url, vocabulary_id)
        print(total_count)
        if total_count is not None:
            content = f"The total 'count' value from '{base_url}' is: {total_count} terms"
            response = Response(content, status=200, mimetype='text/plain')
            response.headers['Message'] = 'Successfully retrieve term count.'
            response.headers['Content-Disposition'] = 'attachment; filename="total_count.txt"'
            return response
        else:
            return jsonify({"Failed to retrieve the total 'count' value from the API."}), 400
    else:
        return jsonify({"error": "Please provide 'base_url' and 'vocabulary_id' in the request body."}), 400


# API endpoint to download RDF content
@app.route('/get_vocabulary', methods=['POST'])
def download_content():
    base_url = request.form.get('base_url')
    vocabulary_id = request.form.get('vocabulary_id')
    rdf_content, content_type = download_rdf_content(base_url, vocabulary_id)
    if rdf_content:
        file_extension = '.rdf' if content_type == 'application/rdf+xml' else '.ttl'
        response = Response(rdf_content, status=200, mimetype=content_type)
        response.headers['Content-Disposition'] = f'attachment; filename={vocabulary_id}{file_extension}'
        response.headers['Message'] = 'Vocabulary successfully downloaded.'
        return response
    else:
        return jsonify({"message": "Failed to download RDF content"}), 500


@app.route('/skos_verify', methods=['POST'])
def skos_verify():
    uploaded_file = request.files['vocabulary_id']
    if uploaded_file:
        # Create a temporary file to save the uploaded file
        with NamedTemporaryFile(delete=False, suffix='.rdf') as temp_file:
            uploaded_file.save(temp_file)
            temp_file_path = temp_file.name
        print(temp_file_path)
        output = skos_rdf_validate(temp_file_path)

    if output:
        output_json = json.dumps({"file": temp_file_path, "valid": True})
        os.remove(temp_file_path)
        # Return with 200 OK status for successful validation
        return jsonify({"success": True, "message": "Validation performed"}), 200
        response = Response(output_json, status=200, mimetype="application/json")
        response.headers['Content-Disposition'] = 'attachment; filename="file.json"'
        response.headers['Message'] = 'Vocabulary successfully downloaded.'
        return response
    else:
        # Return with 400 Bad Request status for failed validation
        return jsonify({"success": False, "warnings": output, "message": "Validation failed"}), 400


if __name__ == '__main__':
    app.run(port=5003, debug=True)
