# import click
# import multiprocessing
# import gunicorn.app.base
# from prov.app import init_api
# from gunicorn.six import iteritems
#
#
# @click.command()
# @click.option('--host', default='127.0.0.1', help='provservice host.')
# @click.option('--port', default=7030, help='provservice server port.')
# @click.option('--workers', default=2, help='provservice server workers.')
# @click.option('--log', default='logs/server.log', help='log file for app.')
# def cli(host, port, log, workers):
#     """Run the server with options."""
#     options = {
#         'bind': '{0}:{1}'.format(host, port),
#         'workers': workers,
#         'daemon': 'True',
#         'errorlog': log
#     }
#     PROVService(init_api(), options).run()
#
#
# class PROVService(gunicorn.app.base.BaseApplication):
#     """Create Standalone Application Provenance Service."""
#
#     def __init__(self, app, options=None):
#         """The init."""
#         self.options = options or {}
#         self.application = app
#         super(PROVService, self).__init__()
#
#     def load_config(self):
#         """Load configuration."""
#         config = dict([(key, value) for key, value in iteritems(self.options)
#                        if key in self.cfg.settings and value is not None])
#         for key, value in iteritems(config):
#             self.cfg.set(key.lower(), value)
#
#     def load(self):
#         """Load configuration."""
#         return self.application
#
#
# # Unless really needed to scale use this function. Otherwise 2 workers suffice.
# def number_of_workers():
#     """Establish the numberb or workers based on cpu_count."""
#     return (multiprocessing.cpu_count() * 2) + 1
#
#
# def main():
#     """Main function."""
#     cli()
#
#
# if __name__ == '__main__':
#     main()
import json
import logging

from twisted.internet import defer, reactor

from stompest.config import StompConfig
from stompest.protocol import StompSpec

from stompest.async import Stomp
from stompest.async.listener import SubscriptionListener
from prov.applib.construct_prov import construct_provenance


class Consumer(object):
    """Consumer of the Provenance messages."""

    QUEUE = '/queue/provenance.inbox'
    ERROR_QUEUE = '/queue/testConsumerError'

    def __init__(self, config=None):
        """Init of the class."""
        if config is None:
            config = StompConfig('tcp://localhost:61613')
        self.config = config

    @defer.inlineCallbacks
    def run(self):
        """Callback function for async consumer."""
        client = Stomp(self.config)
        yield client.connect()
        headers = {
            # client-individual mode is necessary for concurrent processing
            # (requires ActiveMQ >= 5.2)
            StompSpec.ACK_HEADER: StompSpec.ACK_AUTO,
            # the maximal number of messages the broker will let you work on at the same time
            'activemq.prefetchSize': '100',
        }
        client.subscribe(self.QUEUE, headers, listener=SubscriptionListener(self.consume, errorDestination=self.ERROR_QUEUE))

    def consume(self, client, frame):
        """Consume and construct the provenance."""
        """
        NOTE: you can return a Deferred here
        """
        # print "hello"
        parsed = json.loads(frame.body.decode())
        # print parsed
        response = construct_provenance(parsed["provenance"], parsed["payload"])
        print response
        # print('Received frame with count %d' % data['count'])


def main():
    """Main function."""
    logging.basicConfig(level=logging.DEBUG)
    Consumer().run()
    reactor.run()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
