import amqpstorm
from amqpstorm import Message


class RpcClient(object):
    """RPC Client for Prov Service."""

    def __init__(self, hostname='127.0.0.1',
                 username='guest', password='guest',
                 rpc_queue='base.rpc_queue'):
        """Client init function."""
        self.hostname = hostname
        self.username = username
        self.password = password
        self.rpc_queue = rpc_queue
        self.channel = None
        self.response = None
        self.connection = None
        self.callback_queue = None
        self.correlation_id = None
        self.open()

    def open(self):
        """Open communication channel.

        :return:
        """
        self.connection = amqpstorm.Connection(self.hostname,
                                               self.username,
                                               self.password)

        self.channel = self.connection.channel()

        result = self.channel.queue.declare(exclusive=True)
        self.callback_queue = result['queue']

        self.channel.basic.consume(self._on_response, no_ack=True,
                                   queue=self.callback_queue)

    def close(self):
        """Close communication channel.

        :return:
        """
        self.channel.stop_consuming()
        self.channel.close()
        self.connection.close()

    def call(self, message):
        """Publish message call.

        :return:
        """
        self.response = None
        message = Message.create(self.channel, body=str(message))
        message.reply_to = self.callback_queue
        self.correlation_id = message.correlation_id
        message.publish(routing_key=self.rpc_queue)

        while not self.response:
            self.channel.process_data_events(to_tuple=False)
        return int(self.response)

    def _on_response(self, message):
        """Handle response."""
        if self.correlation_id != message.correlation_id:
            return
        self.response = message.body
