# Flask-Based Web Application for a FAIR Digtial Object and graph-based Client Framework

## Overview
This web application is built using Flask and integrates various backend services for data processing and interaction with FAIR Digital Object (FDO) services, mainly a Typed PID Maker (TPM), and a graph database. It is designed for complex data and algorithm management tasks, including SPARQL querying, FDO kernel validation and evaluation, operation execution, and local data handling.

## Components

### Python Modules
- `user_interface.py`: Manages the web interface, processes user requests, and renders HTML templates.
- `sparql_service.py`: Executes and constructs SPARQL queries.
- `query_processing.py`: Restructures SPARQL query results.
- `tpm_interface.py`: Manages interactions with the TPM service and SSH connections to retrieve PID records of FDOs. Provides alternatively access to locally stored JSON records of PIDs.
- `kernel_workflow.py`: Handles data validation against predefined key-value pairs and data record keys.
- `record_mapper.py`: Maps records to requests and processes JSON-like strings.
- `ops_executor.py`: Executes operation requests via HTTP and processes responses.

### HTML Templates
- `submit_sparql.html`: For submitting terms for pre-defined SPARQL queries in the `sparql_service.py` module.
- `select_attributes.html`: For selecting operations associated with attributes based on queries.
- `select_profiles.html`: For selecting operations associated with profiles based on queries.
- `display_response.html`: For displaying operation results, including local storage directory.

### Configuration Files
- `services.json`: Configuration for the graph database and TPM.
- `tpm_keys_config_path.json`: Key mappings for operation access protocols.

### Example Operations
- `example_operations/dh_api.py`: Provides API endpoints for operations related to an exemplary application case of training data composition for ontology matching in Digital Humanities.
- `example_operations/mri_api.py`: Provides API endpoints for operations related to an exemplary application case of training data composition for image classification in Material Sciences.

## User Guide

### Setting Up
1. **Configure** the application using `services.json`, i.e., provide the endoint to the FDO graph-database, as well as the TPM instance or alternatively the local JSON records, and `tpm_keys_config_path.json`, i.e., provide the PIDs according to the Data Type Registry entries used to create the FDOs.
2. **Run** the Flask server via `user_interface.py`.

### Using the Application
1. **Submit SPARQL Queries**: Access the `submit_sparql.html` form, choose a query type, enter values, and submit.
2. **Select Profiles or Attributes**: Use the `select_profiles.html` or `select_attributes.html` templates to make selections for operations and resulting output types based on query results.
3. **View Operation Results**: Results and details of operations are displayed on `display_response.html`.

### Technical Aspects
- **Data Validation**: Validates data records against TPM keys with various checks for accessibility, up-to-dateness, checksum inetgrity, and lisence reusability for digital objects.
- **SPARQL Querying**: Executes and constructs queries for data retrieval.
- **Operation Execution**: Manages the execution of TPM-defined operations.

### Walking Example
- The following figure shows an example for querying the graph using a profile name:
  ![Alt text](https://github.com/kit-data-manager/FAIR-Digital-Object-Client-Framework-Implementation/blob/main/profiles_query_ex.png)
- The following figure shows an example for querying the graph using an attribute name:
  ![Alt text](https://github.com/kit-data-manager/FAIR-Digital-Object-Client-Framework-Implementation/blob/main/attributes_query_ex.png)
- The following figure shows an example for an operation result, triggered by a previous query and displaying the option to request a new query:
  ![Alt text](https://github.com/kit-data-manager/FAIR-Digital-Object-Client-Framework-Implementation/blob/main/operation_results_ex.png)
  
