import click
import multiprocessing
import schedule
import time
import gunicorn.app.base
from prov.app import init_api
from prov.utils.queue import init_celery
from prov.applib.messaging import Consumer
# from prov.api.index import execute_indexing
from prov.utils.broker import broker
from celery.bin import worker
from gunicorn.six import iteritems
# from prov.utils.logs import app_logger
from os import environ

interval = {'timer': environ['QTIME'] if 'QTIME' in environ else 10}


@click.group()
def cli():
    """Run cli tool."""
    pass


@cli.command('server')
@click.option('--host', default='127.0.0.1', help='provservice host.')
@click.option('--port', default=7030, help='provservice server port.')
@click.option('--workers', default=2, help='provservice server workers.')
@click.option('--log', default='logs/server.log', help='log file for app.')
def server(host, port, log, workers):
    """Run web server with options."""
    options = {
        'bind': '{0}:{1}'.format(host, port),
        'workers': workers,
        'daemon': 'True',
        'errorlog': log
    }
    PROVService(init_api(), options).run()


@cli.command('queue')
@click.option('--address', default=broker['host'], help='message broker host.')
@click.option('--user', default=broker['user'], help='message broker user.')
@click.option('--password', default=broker['pass'], help='message broker password.')
def queue(user, password, address):
    """Task execution with options."""
    queue = worker.worker(app=init_celery(user, password, address))
    options = {
        'broker': 'amqp://{0}:{1}@{2}:5672//'.format(user, password, address),
        'loglevel': 'INFO',
        'traceback': True,
    }
    queue.run(**options)


@cli.command('consumer')
def consumer():
    """Consuming some messages."""
    consumer_init = Consumer(broker['host'], broker['user'], broker['pass'], broker['queue'])
    consumer_init.start()


@cli.command('indexer')
def publisher():
    while True:
        schedule.run_pending()
        time.sleep(1)


class PROVService(gunicorn.app.base.BaseApplication):
    """Create Standalone Application Provenance Service."""

    def __init__(self, app, options=None):
        """The init."""
        self.options = options or {}
        self.application = app
        super(PROVService, self).__init__()

    def load_config(self):
        """Load configuration."""
        config = dict([(key, value) for key, value in iteritems(self.options)
                       if key in self.cfg.settings and value is not None])
        for key, value in iteritems(config):
            self.cfg.set(key.lower(), value)

    def load(self):
        """Load configuration."""
        return self.application


# Unless really needed to scale use this function. Otherwise 2 workers suffice.
def number_of_workers():
    """Establish the number or workers based on cpu_count."""
    return (multiprocessing.cpu_count() * 2) + 1


def main():
    """Main function."""
    cli()


if __name__ == '__main__':
    main()
