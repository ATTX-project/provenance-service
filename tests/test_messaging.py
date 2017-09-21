import unittest
# from rdflib import Graph
from mock import patch
from prov.utils.messaging import Consumer
from prov.utils.broker import broker
from pytest_rabbitmq import factories

rabbitmq_my_proc = factories.rabbitmq_proc(port=5672, logsdir='/tmp')
rabbitmq_my = factories.rabbitmq('rabbitmq_my_proc')


class MessagingTestCase(unittest.TestCase):
    """Test for Messaging."""

    def setUp(self):
        """Set up test fixtures."""
        pass

    @patch.object(Consumer, 'start')
    def test_store_prov_called(self, mock):
        """Test if store_provenance was called."""
        CONSUMER = Consumer(broker['host'], broker['user'], broker['pass'], broker['queue'])
        CONSUMER.start()
        self.assertTrue(mock.called)
