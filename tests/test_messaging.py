import unittest
# from rdflib import Graph
from mock import patch
from prov.utils.messaging import Consumer
# from amqpstorm import Connection
# from amqpstorm.tests.utility import FakeConnection
# from amqpstorm import Channel
# from pytest_rabbitmq import factories
#
# rabbitmq_my_proc = factories.rabbitmq_proc(port=5672, logsdir='/tmp')
# rabbitmq_my = factories.rabbitmq('rabbitmq_my_proc')


class MessagingTestCase(unittest.TestCase):
    """Test for Messaging."""

    def setUp(self):
        """Set up test fixtures."""
        pass

    @patch.object(Consumer, 'start')
    def test_start_consumer(self, mock):
        """Test if start a consumer was called."""
        CONSUMER = Consumer()
        CONSUMER.start()
        self.assertTrue(mock.called)
