import json
import unittest
from rdflib import Graph, URIRef
from prov.applib.construct_prov import prov_task, Provenance
# from prov.utils.prefixes import ATTXProv
from mock import patch
from prov.applib.graph_store import GraphStore


class ProvenanceTestCase(unittest.TestCase):
    """Test for Provenance function."""

    def setUp(self):
        """Set up test fixtures."""
        self.graph = Graph()
        pass

    @patch.object(GraphStore, '_graph_add')
    def test_store_prov_called(self, mock):
        """Test if store_provenance was called."""
        with open('tests/resources/prov_request.json') as datafile:
            graph_data = json.load(datafile)
        prov = Provenance(graph_data["provenance"], graph_data["payload"])
        prov._construct_provenance()
        self.assertTrue(mock.called)

    def test_store_prov_bad(self):
        """Test KeyError was raised."""
        with open('tests/resources/prov_request_bad.json') as datafile:
            graph_data = json.load(datafile)
        prov = Provenance(graph_data["provenance"], graph_data["payload"])
        with self.assertRaises(KeyError):
            prov._construct_provenance()

    @patch.object(Provenance, '_construct_provenance')
    def test_prov_data_stored(self, mock):
        """Test the resulting provenance graph."""
        with open('tests/resources/prov_request.json') as datafile:
            graph_data = json.load(datafile)
        prov_task(graph_data["provenance"], graph_data["payload"])
        self.assertTrue(mock.called)

    @patch.object(GraphStore, '_graph_add')
    def test_prov_describe_data_stored(self, mock):
        """Test the resulting provenance describe dataset."""
        with open('tests/resources/prov_request_describe.json') as datafile:
            graph_data = json.load(datafile)
        with open('tests/resources/prov_output_describe.ttl') as datafile1:
            graph_output = datafile1.read()
        prov_task(graph_data["provenance"], graph_data["payload"])
        mock.assert_called_with(URIRef("http://data.hulib.helsinki.fi/prov_workflowingestionwf_activity1"), graph_output)

    @patch.object(GraphStore, '_graph_add')
    def test_prov_communication_data_stored(self, mock):
        """Test the resulting provenance describe dataset."""
        with open('tests/resources/prov_request_communication.json') as datafile:
            graph_data = json.load(datafile)
        with open('tests/resources/prov_output_communication.ttl') as datafile1:
            graph_output = datafile1.read()
        prov_task(graph_data["provenance"], graph_data["payload"])
        # mock.assert_called_with(ATTXProv, graph_output)
        mock.assert_called_with(URIRef("http://data.hulib.helsinki.fi/prov_workflowingestionwf_activity1"), graph_output)

    @patch.object(GraphStore, '_graph_add')
    def test_prov_workflow_data_stored(self, mock):
        """Test the resulting provenance describe dataset."""
        with open('tests/resources/prov_request_workflow.json') as datafile:
            graph_data = json.load(datafile)
        with open('tests/resources/prov_output_workflow.ttl') as datafile1:
            graph_output = datafile1.read()
        prov_task(graph_data["provenance"], graph_data["payload"])
        mock.assert_called_with(URIRef("http://data.hulib.helsinki.fi/prov_workflowingestionwf_activity1"), graph_output)


if __name__ == "__main__":
    unittest.main()
