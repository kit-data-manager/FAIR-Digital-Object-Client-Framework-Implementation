class QueryProcessing:
    def __init__(self):
        pass

    def restructure_query_result(self, query_result):
        """
        Restructures the query result into a nested dictionary structure.

        Args:
            query_result (dict): The query result to be restructured.

        Returns:
            dict: The restructured query result.
        """
        result_dict = {}  # Initialize an empty dictionary to hold the results

        for binding in query_result['results']['bindings']:  # Loop through each binding in the query result
            keys = []  # Initialize an empty list to hold the keys for this binding

            for var in query_result['head']['vars']:  # Loop through each variable in the query result header
                try:
                    keys.append(binding[var]['value'])  # Try to append the value of the variable to the keys list
                except KeyError:
                    # If the variable is missing, append a None value to the keys list
                    keys.append(None)

            # Build the nested dictionary structure
            d = result_dict
            for key in keys[:-2]:
                d = d.setdefault(key, {})
            d = d.setdefault(keys[-2], [])
            d.append(keys[-1])

        return result_dict