import json
import falcon
from prov.utils.logs import app_logger
from prov.applib.construct_index import index_task


class IndexProv(object):
    """Index Provenance in Elasticsearch on request."""

    def on_post(self, req, resp, parsed):
        """POST request to index provenance documents in Elasticsearch."""
        response = index_task.delay(parsed["provenance"], parsed["payload"])
        result = {'task_id': response.id}
        resp.body = json.dumps(result)
        resp.content_type = 'application/json'
        resp.status = falcon.HTTP_200
        app_logger.info('Accepted POST Request for /index/prov.')
