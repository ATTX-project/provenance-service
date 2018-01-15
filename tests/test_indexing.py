# import json
import unittest
from rdflib import Graph
from prov.applib.construct_index import index_task, ProvenanceIndex
from prov.utils.broker import broker
from mock import patch
from prov.applib.graph_store import GraphStore
from requests.exceptions import ConnectionError


class ProvenanceTestCase(unittest.TestCase):
    """Test for Provenance function."""

    def setUp(self):
        """Set up test fixtures."""
        self.graph = Graph()
        pass

    @patch.object(GraphStore, '_prov_list')
    def test_index_list_called(self, mock_list):
        """Test if store_provenance list was called."""
        prov = ProvenanceIndex(broker["framequeue"], broker["indexqueue"])
        prov._index_prov()
        self.assertTrue(mock_list.called)

    def test_index_bad(self):
        """Test ConnectionError was raised."""
        prov = ProvenanceIndex(broker["framequeue"], broker["indexqueue"])
        with self.assertRaises(ConnectionError):
            prov._index_prov()

    @patch.object(ProvenanceIndex, '_index_prov')
    def test_index_called(self, mock):
        """Test the index operation was called."""
        index_task()
        self.assertTrue(mock.called)


if __name__ == "__main__":
    unittest.main()
