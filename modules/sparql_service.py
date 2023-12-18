import requests

class SPARQLService:
    def __init__(self, endpoint_config):
        """
        Initializes the SPARQLService with the provided endpoint configuration.

        Args:
            endpoint_config (str): The endpoint configuration.
        """
        self.endpoint = endpoint_config

    def execute_query(self, query):
        """
        Executes a SPARQL query.

        Args:
            query (str): The SPARQL query to execute.

        Returns:
            dict or str: The results of the query if successful, or an error message if failed.
        """
        # Set up the headers for the HTTP request
        headers = {
            "Accept": "application/sparql-results+json",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        }

        # Issue the HTTP POST request to execute the SPARQL query
        response = requests.post(self.endpoint, headers=headers, data={"query": query})

        # Check for a valid response and return the results or error message
        if response.status_code == 200:
            results = response.json()
            return results
        else:
            return f"Failed to execute SPARQL query. Status code: {response.status_code}"

    def construct_query1(self, profile_names):
        """
        Constructs a SPARQL query to retrieve information about profiles and related FDOs.

        Args:
            profile_names (str): Comma-separated names of profiles.

        Returns:
            str: The constructed SPARQL query.
        """
        # Join the profile names into a SPARQL VALUES clause
        values_clause = ' '.join(f'"{name}"' for name in profile_names.split(','))

        sparql_query = f"""
        PREFIX fdoo: <https://anonymized.org/FDO-Graph#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?profileName ?operationName ?operationLabel ?outputName ?outputLabel ?fdoLabel
        WHERE {{
        # Define the local names of profiles to match
        VALUES ?profileLocalName {{ {values_clause} }} # Add more profile names as needed

        # Match profiles by local name
        ?profile a fdoo:Profile .
        BIND(REPLACE(STR(?profile), "https://anonymized.org/FDO-Graph#", "") AS ?profileName)
        FILTER(?profileLocalName IN (?profileName))

        # Match FDOs related to profiles
        ?fdo a fdoo:FDO ; fdoo:hasProfile ?profile ; rdfs:label ?fdoLabel .
        
        # Match operations related to FDOs and retrieve their labels
        ?operation a fdoo:Operation ; fdoo:isOperationFor ?fdo ; rdfs:label ?operationLabel .
        BIND(REPLACE(STR(?operation), "https://anonymized.org/FDO-Graph#", "") AS ?operationName)
        # Match attributes returned by operations
        ?operation fdoo:returns ?attribute .
        ?attribute a fdoo:Attribute ; rdfs:label ?outputLabel
        BIND(REPLACE(STR(?attribute), "https://anonymized.org/FDO-Graph#", "") AS ?outputName)
        }}
        """
        return sparql_query

    def construct_query2(self, attributes):
        """
        Constructs a SPARQL query to retrieve information about attributes and related operations.

        Args:
            attributes (str): Comma-separated names of attributes.

        Returns:
            str: The constructed SPARQL query.
        """
        attributes_str = ' '.join(f'"{name}"' for name in attributes.split(','))
        # SPARQL query template with placeholders for attributes
        sparql_query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX fdoo: <https://anonymized.org/FDO-Graph#>

        SELECT ?attributeName ?operationName ?operationLabel ?outputAttributeName ?outputAttributeLabel
        WHERE {{
            VALUES ?attributeLocalName {{ {attributes_str} }}
            ?attribute a fdoo:Attribute .
            BIND(REPLACE(STR(?attribute), "https://anonymized.org/FDO-Graph#", "") AS ?attributeName)
            FILTER(?attributeLocalName IN (?attributeName))

            ?inputSet a fdoo:Input_Set ; fdoo:containsAttribute ?attribute .
            
            OPTIONAL {{
            ?inputSet fdoo:hasValue ?recordValue .
            ?recordValue fdoo:hasKey ?keyAttribute .
            FILTER (?keyAttribute = ?attribute || EXISTS {{
                ?keyAttribute fdoo:inheritsToAttribute ?attribute .
                }})
            }}
            
            ?operation a fdoo:Operation ; fdoo:requires ?inputSet ; rdfs:label ?operationLabel .
            BIND(REPLACE(STR(?operation), "https://anonymized.org/FDO-Graph#", "") AS ?operationName)
            ?operation a fdoo:Operation ; fdoo:returns ?outputAttribute .
            ?outputAttribute rdfs:label ?outputAttributeLabel
            BIND(REPLACE(STR(?outputAttribute), "https://anonymized.org/FDO-Graph#", "") AS ?outputAttributeName)
        }}
        """
        return sparql_query
