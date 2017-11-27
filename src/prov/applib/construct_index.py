from prov.utils.queue import init_celery
from prov.utils.broker import broker

app = init_celery(broker['user'], broker['pass'], broker['host'])


@app.task(name="construct.index", max_retries=5)
def index_task(prov_object, payload):
    """Parse Provenance Object and construct Provenance Graph."""
    # prov = Provenance(prov_object, payload)
    # result = prov._construct_provenance()
    # return result
    pass
