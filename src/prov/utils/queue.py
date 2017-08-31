from celery import Celery
# from prov.utils.logs import app_logger


def init_celery(user, password, host):
    """Start Task queue."""
    # app_logger.info('ProvService Celery queue backend is running.')
    app = Celery('prov_service')
    app.conf.update(
        BROKER_URL='amqp://{0}:{1}@{2}:5672//'.format(user, password, host),
        CELERY_RESULT_BACKEND='db+sqlite:///results.sqlite',
        CELERY_RESULT_PERSISTENT=True,
        CELERYD_REDIRECT_STDOUTS_LEVEL='INFO'
    )
    return app
