import json
import falcon
from prov.schemas import load_schema
from prov.utils.validate import validate
from prov.utils.logs import app_logger
from celery.result import AsyncResult


class RetrieveQueueTask(object):
    """Update Provenance on request."""

    @validate(load_schema('idtype'))
    def on_get(self, req, resp, task_id):
        """Respond on GET request to queued task endpoint."""
        task_output = AsyncResult(task_id)
        result = {'status': task_output.status.lower(), 'output': str(task_output.result)}
        resp.status = falcon.HTTP_200
        resp.body = json.dumps(result)
        app_logger.info('Finished operations on /status/task/{0} GET Request.'.format(task_id))
