import unittest
from urllib import quote
import responses
# import requests
import json
from falcon import testing
from prov.app import init_api
from prov.utils.graph_store import GraphStore


class GraphStoreTest(testing.TestCase):
    """Testing GM prov function and initialize it for that purpose."""

    def setUp(self):
        """Setting the app up."""
        self.app = init_api()

    def tearDown(self):
        """Tearing down the app up."""
        pass


class GraphTestCase(GraphStoreTest):
    """Test for DB connection."""

    def test_create(self):
        """Test GET health message."""
        self.app
        pass

    def setUp(self):
        """Set up test fixtures."""
        self.server_address = "http://localhost:3030/$/"
        self.request_address = "http://localhost:3030/ds/"
        self.api = "http://localhost:7030/"
        self.version = "0.1"

    @responses.activate
    def test_ping(self):
        """Test_ping on graph endpoint."""
        responses.add(responses.GET, "http://localhost:3030/{0}/ping".format("$"), "2017-09-18T11:41:19.915+00:00", status=200)
        fuseki = GraphStore()
        resp = fuseki.graph_health()
        self.assertTrue(resp)

    @responses.activate
    def test_graph_list(self):
        """Test graph list on graph endpoint."""
        list_query = quote("select ?g (count(*) as ?count) {graph ?g {?s ?p ?o}} group by ?g")
        with open('tests/resources/graph_list_request.json') as datafile1:
            graph_data = json.load(datafile1)
        with open('tests/resources/graph_list_response.json') as datafile2:
            graph_list = json.load(datafile2)
        responses.add(responses.GET, "{0}sparql?query={1}".format(self.request_address, list_query), json=graph_data, status=200)
        # responses.add(responses.GET, "{0}{1}/graph/statistics".format(self.api, self.version), json=graph_list, status=200)
        # resp = requests.get("{0}{1}/graph/statistics".format(self.api, self.version))
        # assert(resp.text == graph_list)
        # fuseki = GraphStore()
        # resp2 = fuseki.graph_list()
        assert(resp2 == graph_list)


if __name__ == "__main__":
    unittest.main()


# {
#     "dataset": "/ds",
#     "requests": {
#         "failedRequests": 0,
#         "totalRequests": 1
#     },
#     "totalTriples": 388
# }
