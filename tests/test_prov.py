import json
import unittest
from rdflib import Graph
from prov.applib.construct_prov import prov_task, Provenance
from mock import patch
# from prov.applib.graph_store import GraphStore


class ProvenanceTestCase(unittest.TestCase):
    """Test for Provenance function."""

    def setUp(self):
        """Set up test fixtures."""
        self.graph = Graph()
        pass

    # @patch.object(GraphStore, '_graph_add')
    # def test_store_prov_called(self, mock):
    #     """Test if store_provenance was called."""
    #     store_provenance(self.graph)
    #     self.assertTrue(mock.called)

    # @patch.object(Provenance, 'construct_provenance')
    # @patch.object(Provenance, 'store_provenance')
    # def test_store_prov_bad(self, mock, mock1):
    #     """Test KeyError was raised."""
    #     with open('tests/resources/prov_request_bad.json') as datafile:
    #         graph_data = json.load(datafile)
    #     with self.assertRaises(KeyError):
    #         prov_task(graph_data["provenance"], graph_data["payload"])

    @patch.object(Provenance, 'construct_provenance')
    def test_prov_data_stored(self, mock):
        """Test the resulting provenance graph."""
        with open('tests/resources/prov_request.json') as datafile:
            graph_data = json.load(datafile)
        prov_task(graph_data["provenance"], graph_data["payload"])
        self.assertTrue(mock.called)
    #
    # @patch.object(Provenance, 'construct_provenance')
    # def test_prov_describe_data_stored(self, mock):
    #     """Test the resulting provenance describe dataset."""
    #     with open('tests/resources/prov_request_describe.json') as datafile:
    #         graph_data = json.load(datafile)
    #     with open('tests/resources/prov_output_describe.ttl') as datafile1:
    #         graph_output = datafile1.read()
    #     prov_task(graph_data["provenance"], graph_data["payload"])
    #     mock.assert_called_with(graph_output)
    #
    # @patch.object(Provenance, 'construct_provenance')
    # def test_prov_communication_data_stored(self, mock):
    #     """Test the resulting provenance describe dataset."""
    #     with open('tests/resources/prov_request_communication.json') as datafile:
    #         graph_data = json.load(datafile)
    #     with open('tests/resources/prov_output_communication.ttl') as datafile1:
    #         graph_output = datafile1.read()
    #     prov_task(graph_data["provenance"], graph_data["payload"])
    #     mock.assert_called_with(graph_output)
    #
    # @patch.object(Provenance, 'construct_provenance')
    # def test_prov_workflow_data_stored(self, mock):
    #     """Test the resulting provenance describe dataset."""
    #     with open('tests/resources/prov_request_workflow.json') as datafile:
    #         graph_data = json.load(datafile)
    #     with open('tests/resources/prov_output_workflow.ttl') as datafile1:
    #         graph_output = datafile1.read()
    #     prov_task(graph_data["provenance"], graph_data["payload"])
    #     mock.assert_called_with(graph_output)


if __name__ == "__main__":
    unittest.main()
