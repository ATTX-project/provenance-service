import unittest
from urllib import quote
import responses
import json
import httpretty
import falcon
from falcon import testing
from prov.app import init_api


class GraphStoreTest(testing.TestCase):
    """Testing Graph Store API and initialize the app for that."""

    def setUp(self):
        """Setting the app up."""
        self.server_address = "http://localhost:3030/$/"
        self.request_address = "http://localhost:3030/ds"
        self.api = "http://localhost:7030/"
        self.version = "0.2"
        self.app = init_api()

    def tearDown(self):
        """Tearing down the app up."""
        pass


class GraphTestCase(GraphStoreTest):
    """Test for Graph Store operations."""

    def test_create(self):
        """Test create API."""
        self.app
        pass

    @responses.activate
    def test_api_graph_stats(self):
        """Test api graph stats on graph endpoint."""
        list_query = quote("select ?g (count(*) as ?count) {graph ?g {?s ?p ?o}} group by ?g")
        with open('tests/resources/graph_stats_request.json') as datafile1:
            graph_data = json.load(datafile1)
        with open('tests/resources/graph_stats_response.json') as datafile2:
            graph_stats = json.load(datafile2)
        with open('tests/resources/graph_list_request.json') as datafile3:
            graph_list = json.load(datafile3)
        responses.add(responses.GET, "{0}stats/{1}".format(self.server_address, "ds"), json=graph_data, status=200)
        responses.add(responses.GET, "{0}/sparql?query={1}".format(self.request_address, list_query), json=graph_list, status=200)
        responses.add(responses.GET, "{0}{1}/graph/statistics".format(self.api, self.version), json=graph_list, status=200)
        result = self.simulate_get("/{0}/graph/statistics".format(self.version))
        assert(result.status == falcon.HTTP_200)
        assert(result.json == graph_stats)

    @responses.activate
    def test_api_graph_list(self):
        """Test api graph list on graph endpoint."""
        list_query = quote("select ?g (count(*) as ?count) {graph ?g {?s ?p ?o}} group by ?g")
        with open('tests/resources/graph_list_request.json') as datafile1:
            graph_data = json.load(datafile1)
        with open('tests/resources/graph_list_response.json') as datafile2:
            graph_list = json.load(datafile2)
        responses.add(responses.GET, "{0}/sparql?query={1}".format(self.request_address, list_query), json=graph_data, status=200)
        result = self.simulate_get("/{0}/graph/list".format(self.version))
        assert(result.status == falcon.HTTP_200)
        assert(result.json == graph_list)

    @responses.activate
    def test_api_graph_retrieve_None(self):
        """Test api graph retrieve non-existent graph."""
        responses.add(responses.GET, "{0}/data?graph={1}".format(self.request_address, "http://test.com"), status=404)
        params = {"uri": "http://test.com"}
        result = self.simulate_get("/{0}/graph".format(self.version), params=params)
        assert(result.status == falcon.HTTP_410)

    @responses.activate
    def test_api_graph_retrieve(self):
        """Test api graph retrieve a specific graph."""
        with open('tests/resources/graph_strategy.ttl') as datafile:
            graph_data = datafile.read()
        url = "http://data.hulib.helsinki.fi/attx/strategy"
        responses.add(responses.GET, "{0}/data?graph={1}".format(self.request_address, url), body=graph_data, status=200)
        params = {"uri": "http://data.hulib.helsinki.fi/attx/strategy"}
        result = self.simulate_get("/{0}/graph".format(self.version), params=params)
        assert(result.status == falcon.HTTP_200)
        assert(result.text == graph_data)

    @responses.activate
    def test_api_graph_add(self):
        """Test api update graph."""
        url = "http://data.hulib.helsinki.fi/attx/strategy"
        with open('tests/resources/graph_add_request.json') as datafile:
            graph_data = datafile.read().replace('\n', '')
        with open('tests/resources/graph_add_response.json') as datafile:
            response_data = json.load(datafile)

        def request_callback1(request):
            """Request callback for drop graph."""
            headers = {'content-type': "application/json",
                       'cache-control': "no-cache"}
            return (200, headers, json.dumps(response_data))

        responses.add_callback(
            responses.POST, "{0}/data?graph={1}".format(self.request_address, url),
            callback=request_callback1,
            content_type='text/turtle',
        )

        def request_callback2(request):
            """Request callback for drop graph."""
            headers = {'content-type': "application/json",
                       'cache-control': "no-cache"}
            return (200, headers, json.dumps(graph_data))

        responses.add_callback(
            responses.POST, "{0}{1}/graph/update".format(self.api, self.version),
            callback=request_callback2,
            content_type='application/json',
        )
        result = self.simulate_post("/{0}/graph/update".format(self.version), body=graph_data)
        assert(result.status == falcon.HTTP_200)
        assert(result.json == response_data)

    @responses.activate
    def test_api_graph_drop(self):
        """Test api drop graph."""
        with open('tests/resources/graph_drop.txt') as datafile:
            graph_data = datafile.read()

        def request_callback(request):
            """Request callback for drop graph."""
            headers = {'content-type': 'text/html',
                       'cache-control': "no-cache"}
            return (200, headers, graph_data)

        responses.add_callback(
            responses.POST, "{0}/update".format(self.request_address),
            callback=request_callback,
            content_type="application/x-www-form-urlencoded",
        )
        params = {"uri": "http://data.hulib.helsinki.fi/attx/strategy"}
        result = self.simulate_delete("/{0}/graph".format(self.version), params=params)
        assert(result.status == falcon.HTTP_200)

    @httpretty.activate
    def test_api_graph_sparql(self):
        """Test api update graph."""
        with open('tests/resources/graph_sparql.xml') as datafile:
            graph_data = datafile.read()
        with open('tests/resources/graph_query_request.json') as datafile:
            graph_query = datafile.read().replace('\n', '')
        list_query = "select ?g (count(*) as ?count) {graph ?g {?s ?p ?o}} group by ?g"
        url = "default"
        request_url = "{0}/query?default-graph-uri=%s&query={1}&output=xml&results=xml&format=xml".format(self.request_address, url, list_query)
        httpretty.register_uri(httpretty.GET, request_url, graph_data, status=200, content_type="application/sparql-results+xml")
        result = self.simulate_post('/{0}/graph/query'.format(self.version), body=graph_query)
        assert(result.text == graph_data)
        httpretty.disable()
        httpretty.reset()


if __name__ == "__main__":
    unittest.main()
