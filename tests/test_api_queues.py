import unittest
import responses
import falcon
from falcon import testing
from prov.app import init_api


class QueueAPITestCase(testing.TestCase):
    """Testing Queues task."""

    def setUp(self):
        """Setting the app up."""
        self.api = "http://localhost:7030/"
        self.version = "0.2"
        self.app = init_api()

    def tearDown(self):
        """Tearing down the app up."""
        pass


class QueueTestCase(QueueAPITestCase):
    """Test for Graph Store operations."""

    def test_create(self):
        """Test create message."""
        self.app
        pass

    @responses.activate
    def test_api_queue_get(self):
        """Test get specific prov id from endpoint."""
        responses.add(responses.GET, "{0}{1}/status/task/{2}".format(self.api, self.version, "123"), status=200)
        result = self.simulate_get("/{0}/status/task/{1}".format(self.version, "123"))
        assert(result.status == falcon.HTTP_200)


if __name__ == "__main__":
    unittest.main()
