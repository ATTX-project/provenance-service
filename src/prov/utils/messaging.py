# import pika
import json
from amqpstorm import Connection
from prov.applib.construct_prov import construct_provenance


# class PikaMessaging(object):
#     """Handle RabbitMQ communication."""
#
#     def __init__(self):
#         """Init function for message broker connection."""
#         self.credentials = pika.PlainCredentials('user', 'password')
#         self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', 5672, '/', self.credentials))
#
#         self.channel = self.connection.channel()
#
#         result = self.channel.queue_declare(exclusive=True)
#         self.callback_queue = result.method.queue
#
#         self.channel.basic_consume(self.on_response, no_ack=True,
#                                    queue=self.callback_queue)


def on_message(body, channel, method, properties):
    """Function is called when a message is received.

    :param bytes|str|unicode body: Message payload
    :param Channel channel: AMQPStorm Channel
    :param dict method: Message method
    :param dict properties: Message properties
    :return:
    """
    prov = json.loads(body)
    response = construct_provenance.delay(prov["provenance"], prov["payload"])
    result = {'task_id': response.id}
    print(result)
    # print("Message:", prov["provenance"])

    # Acknowledge that we handled the message without any issues.
    channel.basic.ack(delivery_tag=method['delivery_tag'])


def consumer(host, user, password):
    """Typical consumer."""
    with Connection(host, user, password) as connection:
        with connection.channel() as channel:
            # Declare the Queue, 'simple_queue'.
            channel.queue.declare('simple_queue')

            # Set QoS to 100.
            # This will limit the consumer to only prefetch a 100 messages.

            # This is a recommended setting, as it prevents the
            # consumer from keeping all of the messages in a queue to itself.
            channel.basic.qos(100)

            # Start consuming the queue 'simple_queue' using the callback
            # 'on_message' and last require the message to be acknowledged.
            channel.basic.consume(on_message, 'simple_queue', no_ack=False)

            try:
                # Start consuming messages.
                # to_tuple equal to True means that messages consumed
                # are returned as tuple, rather than a Message object.
                channel.start_consuming(to_tuple=True)
            except KeyboardInterrupt:
                channel.close()


if __name__ == '__main__':
    consumer()
