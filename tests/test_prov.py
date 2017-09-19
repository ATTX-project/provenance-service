import json
import unittest
# from prov.app import init_api
from rdflib import Graph
from prov.applib.construct_prov import construct_provenance


class ProvenanceTestCase(unittest.TestCase):
    """Test for DB connection."""

    def test_create(self):
        """Test GET health message."""
        # self.app
        self.graph = Graph()
        pass

    def setUp(self):
        """Set up test fixtures."""
        pass

    def construct_provenance_test(self):
        """Test the resulting provenance graph."""
        with open('tests/resources/prov_request.json') as datafile:
            graph_data = json.load(datafile)
        with open('tests/resources/prov_output.ttl') as datafile1:
            graph_output = datafile1.read()
        output = construct_provenance(graph_data["provenance"], graph_data["payload"])
        assert(output == graph_output)


if __name__ == "__main__":
    unittest.main()
