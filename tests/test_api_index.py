import unittest
# import responses
# import json
# import httpretty
# import falcon
from falcon import testing
from prov.app import init_api


class APIIndexTest(testing.TestCase):
    """Testing Graph Store API and initialize the app for that."""

    def setUp(self):
        """Setting the app up."""
        self.server_address = "http://localhost:3030/$/"
        self.request_address = "http://localhost:3030/ds"
        self.API = "http://localhost:7030/"
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


if __name__ == "__main__":
    unittest.main()
