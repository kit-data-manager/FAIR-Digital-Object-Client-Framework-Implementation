import unittest
from modules.query_processing import QueryProcessing
class QueryProcessingTests(unittest.TestCase):
    def setUp(self):
        self.query_processing = QueryProcessing()

    def test_restructure_query_result_empty(self):
        query_result = {'head': {'vars': []}, 'results': {'bindings': []}}
        expected_result = {}
        result = self.query_processing.restructure_query_result(query_result)
        self.assertEqual(result, expected_result)

    def test_restructure_query_result_single_binding(self):
        query_result = {'head': {'vars': ['var1', 'var2']}, 'results': {'bindings': [{'var1': {'value': 'value1'}, 'var2': {'value': 'value2'}}]}}
        expected_result = {'value1': {'value2': []}}
        result = self.query_processing.restructure_query_result(query_result)
        self.assertEqual(result, expected_result)

    def test_restructure_query_result_multiple_bindings(self):
        query_result = {'head': {'vars': ['var1', 'var2']}, 'results': {'bindings': [{'var1': {'value': 'value1'}, 'var2': {'value': 'value2'}}, {'var1': {'value': 'value3'}, 'var2': {'value': 'value4'}}]}}
        expected_result = {'value1': {'value2': []}, 'value3': {'value4': []}}
        result = self.query_processing.restructure_query_result(query_result)
        self.assertEqual(result, expected_result)

if __name__ == '__main__':
    unittest.main()

