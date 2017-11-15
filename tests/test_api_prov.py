import unittest
import responses
import json
import falcon
from falcon import testing
from prov.app import init_api
from mock import patch, Mock


class ReturnObject(object):
    """Return ids instead of celery class."""

    id = 2151


class ProvenanceAPITestCase(testing.TestCase):
    """Testing Graph Store and initialize the app for that.."""

    def setUp(self):
        """Setting the app up."""
        self.api = "http://localhost:7030/"
        self.version = "0.2"
        self.app = init_api()

    def tearDown(self):
        """Tearing down the app up."""
        pass


class ProvTestCase(ProvenanceAPITestCase):
    """Test for Graph Store operations."""

    def test_create(self):
        """Test create message."""
        self.app
        pass

    @responses.activate
    @patch('prov.api.provenance.prov_task', autospec=True)
    def test_api_prov(self, mock):
        """Test api prov everything ok."""
        with open('tests/resources/prov_request.json') as datafile:
            graph_data = datafile.read().replace('\n', '')

        mock.delay.return_value = Mock()
        response = mock.delay.return_value = ReturnObject()
        data = {"task_id": response.id}

        def request_callback(request):
            """Request callback for drop graph."""
            headers = {'content-type': "application/json",
                       'cache-control': "no-cache"}
            return (200, headers, json.dumps(data))

        responses.add_callback(
            responses.POST, "{0}{1}/prov".format(self.api, self.version),
            callback=request_callback,
            content_type='application/json',
        )

        result = self.simulate_post("/{0}/prov".format(self.version), body=graph_data)
        assert(result.status == falcon.HTTP_200)

    @responses.activate
    @patch('prov.api.provenance.prov_task', autospec=True)
    def test_api_prov_array(self, mock):
        """Test api prov everything ok with array."""
        with open('tests/resources/prov_request_array.json') as datafile:
            graph_data = datafile.read().replace('\n', '')

        mock.delay.return_value = Mock()
        response = mock.delay.return_value = ReturnObject()
        data = {"task_id": [response.id]}

        def request_callback(request):
            """Request callback for drop graph."""
            headers = {'content-type': "application/json",
                       'cache-control': "no-cache"}
            return (200, headers, json.dumps(data))

        responses.add_callback(
            responses.POST, "{0}{1}/prov".format(self.api, self.version),
            callback=request_callback,
            content_type='application/json',
        )

        result = self.simulate_post("/{0}/prov".format(self.version), body=graph_data)
        assert(result.status == falcon.HTTP_200)

    @responses.activate
    def test_api_prov_get(self):
        """Test get specific prov id from endpoint."""
        responses.add(responses.GET, "{0}{1}/prov/show/{2}".format(self.api, self.version, "123"), status=200)
        result = self.simulate_get("/{0}/prov/show/{1}".format(self.version, "123"))
        assert(result.status == falcon.HTTP_200)

    @responses.activate
    def test_api_prov_no_data(self):
        """Test prov validate no data."""
        hdrs = [('Accept', 'application/json'),
                ('Content-Type', 'application/json'), ]
        result = self.simulate_post('/{0}/prov'.format(self.version), body='', headers=hdrs)
        assert(result.status == falcon.HTTP_400)

    @responses.activate
    def test_api_prov_bad(self):
        """Test prov bad input."""
        with open('tests/resources/prov_request_bad.json') as datafile:
            graph_data = datafile.read().replace('\n', '')
        hdrs = [('Accept', 'application/json'),
                ('Content-Type', 'application/json'), ]
        result = self.simulate_post('/{0}/prov'.format(self.version), body=graph_data, headers=hdrs)
        assert(result.status == falcon.HTTP_400)


if __name__ == "__main__":
    unittest.main()
