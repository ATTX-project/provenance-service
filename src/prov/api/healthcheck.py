import json
import falcon
from prov.utils.logs import app_logger
from prov.utils.graph_store import GraphStore

# TO DO More detailed response from the health endpoint with statistics
# For now the endpoint responds with a simple 200


class HealthCheck(object):
    """Create HealthCheck class."""

    def on_get(self, req, resp):
        """Respond on GET request to map endpoint."""
        fuseki = GraphStore()
        if fuseki.health():
            resp.data = json.dumps("\{\"status\":\"OK\"\}", indent=1, sort_keys=True)
        else:
            resp.data = json.dumps("\{\"status\":\"NOT OK\"\}", indent=1, sort_keys=True)
        resp.content_type = 'application/json'
        resp.status = falcon.HTTP_200  # implement 202 when it is needed
        app_logger.info('Finished operations on /health GET Request.')
