import os
import requests

class Ops_Executor:
    def __init__(self):
        pass

    def execute_http_request(self, file_name, request_string, folder_name):
        """
        Executes an HTTP request and saves the response content in a specified folder.

        Args:
            file_name (str): The name of the file.
            request_string (str): The HTTP request string.
            folder_name (str): The name of the folder to save the response content.

        Returns:
            tuple: A tuple containing the status of the request and the folder name.
        """
        
        # Create the folder if it doesn't exist
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        
        request_string = request_string.replace("'", '"')
        
        if "open" in request_string:
            request_string = request_string.replace('"open(', 'open(').replace(', "rb")"', ', "rb")').replace(', "r")"', ', "r")')
        
        print("request_string", request_string)
        
        # Perform the HTTP request
        response = eval(request_string)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Save the response content in the specified folder
            if 'Content-Disposition' in response.headers:
                content_disposition = response.headers['Content-Disposition']
                # Extract filename if present
                if 'filename=' in content_disposition:
                    filename = content_disposition.split('filename=')[1]
                    filename = file_name.replace('/', '_') + filename.replace('"', '').replace("'", '')
            elif 'Content-Type' in response.headers:
                content_type = response.headers.get('Content-Type')

                # Mapping of some common MIME types to file extensions
                mime_type_to_extension = {
                    'application/json': '.json',
                    'application/xml': '.xml',
                    'application/rdf+xml': '.rdf',
                    'application/octet-stream': '.bin',  # Generic binary file
                    'image/jpeg': '.jpg',
                    'image/png': '.png',
                    'text/plain': '.txt',
                    'text/turtle': '.ttl',
                    # Add more mappings as needed
                }

                # Infer the file extension
                filename = mime_type_to_extension.get(content_type, '.unknown')  # Default to '.unknown' if MIME type is not in the dictionary
                filename = file_name.replace('/', '_') + filename.replace('"', '').replace("'", '').replace('/', '_')
            
            with open(os.path.join(folder_name, filename), 'wb') as response_file:
                response_file.write(response.content)
            
            # Store the response in the logging file
            with open('log.txt', 'a') as log_file:
                log_file.write(f'Request: {request_string}\n')
                log_file.write(f'Response: {response.text}\n')
                log_file.write(f'Data stored in: {folder_name}\n')
            
            return 'Request successful', folder_name
        else:
            print("failed")
            return 'Request failed', folder_name