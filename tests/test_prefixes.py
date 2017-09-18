import unittest
from rdflib import Graph, URIRef
from prov.utils.prefixes import bind_prefix, ATTXBase, create_URI


class PrefixTestCase(unittest.TestCase):
    """Test for DB connection."""

    def setUp(self):
        """Set up test fixtures."""
        self.graph = Graph()

    def test_bind_prefix(self):
        """Test for Namespaces."""
        bind_prefix(self.graph)
        self.assertTrue(list(self.graph.namespaces()) != [], "Test if there are namespaces.")

    # def test_namespace(self):
    #     """Test connection."""
    #     namspace_config('file.conf')
    #     pass

    def test_create_URI_2vars(self):
        """Test creating an URI with 2 variables."""
        test_uri = create_URI(ATTXBase, "test")
        assert(test_uri == URIRef("{0}{1}".format(ATTXBase, "test")))

    def test_create_URI_3vars(self):
        """Test creating an URI with 3 variables."""
        test_uri = create_URI(ATTXBase, "test", "add")
        assert(test_uri == URIRef("{0}{1}_{2}".format(ATTXBase, "test", "add")))


if __name__ == "__main__":
    unittest.main()
