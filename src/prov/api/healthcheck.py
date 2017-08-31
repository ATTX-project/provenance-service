import json
import falcon
from prov.utils.logs import app_logger
from prov.utils.graph_store import GraphStore

# TO DO More detailed response from the health endpoint with statistics
# For now the endpoint responds with a simple 200


def healthcheck_response(api_status, graph_health):
    """Content and format health status response."""
    health_status = dict([('provService', api_status)])
    if graph_health:
        health_status['graphStore'] = "Running"
    else:
        health_status['graphStore'] = "Not Running"
    return json.dumps(health_status, indent=1, sort_keys=True)


class HealthCheck(object):
    """Create HealthCheck class."""

    def on_get(self, req, resp):
        """Respond on GET request to map endpoint."""
        fuseki = GraphStore()
        resp.data = healthcheck_response("Running", fuseki.graph_health())
        resp.content_type = 'application/json'
        resp.status = falcon.HTTP_200
        app_logger.info('Finished operations on /health GET Request.')
