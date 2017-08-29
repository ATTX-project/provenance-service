import os
import pika

broker = {'host': os.environ['MHOST'] if 'MHOST' in os.environ else "localhost",
          'user': os.environ['MUSER'] if 'MUSER' in os.environ else "user",
          'pass': os.environ['MKEY'] if 'MKEY' in os.environ else "password"}


class PikaMessaging(object):
    """Handle RabbitMQ communication."""

    def __init__(self):
        """Init function for message broker connection."""
        self.credentials = pika.PlainCredentials('user', 'password')
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', 5672, '/', self.credentials))

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack=True,
                                   queue=self.callback_queue)
