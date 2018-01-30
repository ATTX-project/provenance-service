import unittest
import responses
import json
# import httpretty
import falcon
from falcon import testing
from prov.app import init_api
from mock import patch, Mock


class ReturnObject(object):
    """Return ids instead of celery class."""

    id = 2151


class APIIndexTest(testing.TestCase):
    """Testing Graph Store API and initialize the app for that."""

    def setUp(self):
        """Setting the app up."""
        self.version = "0.2"
        self.app = init_api()

    def tearDown(self):
        """Tearing down the app up."""
        pass


class APIndexTestCase(APIIndexTest):
    """Test for Graph Store API operations."""

    def test_create(self):
        """Test create API."""
        self.app
        pass

    @responses.activate
    @patch('prov.api.index.index_task', autospec=True)
    def test_api_index(self, mock):
        """Test API index everything ok."""
        responses.add(responses.GET, "http://localhost:4303/health", "2018-01-12T11:41:19.915+00:00", status=200)
        responses.add(responses.GET, "http://localhost:4304/health", "2018-01-12T11:41:19.915+00:00", status=200)
        mock.delay.return_value = Mock()
        response = mock.delay.return_value = ReturnObject()
        data = {"task_id": response.id}

        def request_callback(request):
            """Request callback for drop graph."""
            headers = {'content-type': "application/json",
                       'cache-control': "no-cache"}
            return (200, headers, json.dumps(data))

        responses.add_callback(
            responses.POST, "{0}{1}/index/prov".format(self.api, self.version),
            callback=request_callback,
            content_type='application/json',
        )

        result = self.simulate_post("/{0}/index/prov".format(self.version))
        assert(result.status == falcon.HTTP_200)

    @responses.activate
    def test_prov_index_bad(self):
        """Test HTTPBadGateway."""
        result = self.simulate_post("/{0}/index/prov".format(self.version))
        assert(result.status == falcon.HTTP_502)


if __name__ == "__main__":
    unittest.main()
