from celery import Celery
from prov.utils.logs import app_logger


def init_celery(address):
    """Start Task queue."""
    app_logger.info('ProvService Messaging APP is running.')
    app = Celery('prov_service')
    app.conf.update(
        BROKER_URL='amqp://user:password@{0}:5672//'.format(address),
        LOGLEVEL='INFO'
    )
    return app
