import unittest
from unittest.mock import patch
from modules.sparql_service import SPARQLService

class TestSPARQLService(unittest.TestCase):
    def setUp(self):
        self.endpoint_config = "http://example.com/sparql"
        self.sparql_service = SPARQLService(self.endpoint_config)

    def test_execute_query_success(self):
        query = "SELECT * WHERE { ?s ?p ?o }"
        expected_results = {"bindings": []}

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = expected_results

            results = self.sparql_service.execute_query(query)

            self.assertEqual(results, expected_results)

    def test_execute_query_failure(self):
        query = "SELECT * WHERE { ?s ?p ?o }"
        expected_error_message = "Failed to execute SPARQL query. Status code: 500"

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 500

            results = self.sparql_service.execute_query(query)

            self.assertEqual(results, expected_error_message)

    def test_construct_query1(self):
        profile_names = "profile1,profile2"
        expected_query = """
        PREFIX fdoo: <https://datamanager.kit.edu/FDO-Graph#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?profileName ?operationName ?operationLabel ?outputName ?outputLabel ?fdoLabel
        WHERE {
        # Define the local names of profiles to match
        VALUES ?profileLocalName { "profile1" "profile2" } # Add more profile names as needed

        # Match profiles by local name
        ?profile a fdoo:Profile .
        BIND(REPLACE(STR(?profile), "https://datamanager.kit.edu/FDO-Graph#", "") AS ?profileName)
        FILTER(?profileLocalName IN (?profileName))

        # Match FDOs related to profiles
        ?fdo a fdoo:FDO ; fdoo:hasProfile ?profile ; rdfs:label ?fdoLabel .
        
        # Match operations related to FDOs and retrieve their labels
        ?operation a fdoo:Operation ; fdoo:isOperationFor ?fdo ; rdfs:label ?operationLabel .
        BIND(REPLACE(STR(?operation), "https://datamanager.kit.edu/FDO-Graph#", "") AS ?operationName)
        # Match attributes returned by operations
        ?operation fdoo:returns ?attribute .
        ?attribute a fdoo:Attribute ; rdfs:label ?outputLabel
        BIND(REPLACE(STR(?attribute), "https://datamanager.kit.edu/FDO-Graph#", "") AS ?outputName)
        }
        """

        query = self.sparql_service.construct_query1(profile_names)

        self.assertEqual(query.strip(), expected_query.strip())

    def test_construct_query2(self):
        attributes = "attribute1,attribute2"
        expected_query = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX fdoo: <https://datamanager.kit.edu/FDO-Graph#>

        SELECT ?attributeName ?operationName ?operationLabel ?outputAttributeName ?outputAttributeLabel
        WHERE {
            VALUES ?attributeLocalName { "attribute1" "attribute2" }
            ?attribute a fdoo:Attribute .
            BIND(REPLACE(STR(?attribute), "https://datamanager.kit.edu/FDO-Graph#", "") AS ?attributeName)
            FILTER(?attributeLocalName IN (?attributeName))

            ?inputSet a fdoo:Input_Set ; fdoo:containsAttribute ?attribute .
            
            OPTIONAL {
            ?inputSet fdoo:hasValue ?recordValue .
            ?recordValue fdoo:hasKey ?keyAttribute .
            FILTER (?keyAttribute = ?attribute || EXISTS {
                ?keyAttribute fdoo:inheritsToAttribute ?attribute .
                })
            }
            
            ?operation a fdoo:Operation ; fdoo:requires ?inputSet ; rdfs:label ?operationLabel .
            BIND(REPLACE(STR(?operation), "https://datamanager.kit.edu/FDO-Graph#", "") AS ?operationName)
            ?operation a fdoo:Operation ; fdoo:returns ?outputAttribute .
            ?outputAttribute rdfs:label ?outputAttributeLabel
            BIND(REPLACE(STR(?outputAttribute), "https://datamanager.kit.edu/FDO-Graph#", "") AS ?outputAttributeName)
        }
        """

        query = self.sparql_service.construct_query2(attributes)

        self.assertEqual(query.strip(), expected_query.strip())

if __name__ == "__main__":
    unittest.main()
