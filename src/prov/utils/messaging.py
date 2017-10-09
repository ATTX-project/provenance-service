import json
import time
import amqpstorm
from amqpstorm import Connection
from prov.utils.logs import app_logger
from prov.applib.construct_prov import construct_provenance


class Consumer(object):
    """Provenance message consumer."""

    def __init__(self, hostname='127.0.0.1',
                 username='guest', password='guest',
                 queue='base.queue',
                 max_retries=None):
        """Consumer init function."""
        self.hostname = hostname
        self.username = username
        self.password = password
        self.queue = queue
        self.max_retries = max_retries
        self.connection = None

    def create_connection(self):
        """Create a connection.

        :return:
        """
        attempts = 0
        while True:
            attempts += 1
            try:
                self.connection = Connection(self.hostname, self.username, self.password)
                app_logger.info('Established connection with AMQP server {0}'.format(self.connection))
                break
            except amqpstorm.AMQPError as error:
                app_logger.error('Something went wrong: {0}'.format(error))
                if self.max_retries and attempts > self.max_retries:
                    break
                time.sleep(min(attempts * 2, 30))
            except KeyboardInterrupt:
                break

    def start(self):
        """Start the Consumers.

        :return:
        """
        if not self.connection:
            self.create_connection()
        while True:
            try:
                channel = self.connection.channel()
                channel.queue.declare(self.queue)
                channel.basic.consume(self, self.queue, no_ack=False)
                app_logger.info('Connected to queue {0}'.format(self.queue))
                channel.start_consuming(to_tuple=False)
                if not channel.consumer_tags:
                    channel.close()
            except amqpstorm.AMQPError as error:
                app_logger.error('Something went wrong: {0}'.format(error))
                self.create_connection()
            except KeyboardInterrupt:
                self.connection.close()
                break

    def __call__(self, message):
        """Process the message body."""
        try:
            prov = json.loads(message.body)
            if isinstance(prov, dict):
                response = construct_provenance.delay(prov["provenance"], prov["payload"])
                result = {'task_id': response.id}
            elif isinstance(prov, list):
                tasks = []
                for obj in prov:
                    response = construct_provenance.delay(obj["provenance"], obj["payload"])
                    tasks.append(response.id)
                result = {'task_id': tasks}
            app_logger.info('Processed provenance message with result {0}.'.format(result))
        except Exception as error:
            app_logger.error('Something went wrong: {0}'.format(error))
        else:
            message.ack()
