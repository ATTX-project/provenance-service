import json
import falcon
from prov.utils.logs import app_logger
from prov.utils.graph_store import GraphStore
# from amqpstorm.management import ApiConnectionError
# from amqpstorm.management import ApiError
from amqpstorm.management import ManagementApi
from prov.utils.broker import broker

# TO DO More detailed response from the health endpoint with statistics
# For now the endpoint responds with a simple 200


def healthcheck_response(api_status, graph):
    """Content and format health status response."""
    health_status = dict([('provService', api_status)])
    try:
        graph.graph_health()
    except Exception:
        health_status['graphStore'] = "Not Running"
    else:
        health_status['graphStore'] = "Running"
    API = ManagementApi('http://{0}:15672'.format(broker['host']), broker['user'], broker['pass'])
    try:
        result = API.aliveness_test('/')
        if result['status'] == 'ok':
            health_status['messageBroker'] = "Running"
    except Exception:
        health_status['messageBroker'] = "Not Running"
    return json.dumps(health_status, indent=1, sort_keys=True)


class HealthCheck(object):
    """Create HealthCheck class."""

    def on_get(self, req, resp):
        """Respond on GET request to map endpoint."""
        fuseki = GraphStore()
        # if you manange to call this it means the API is running
        resp.data = healthcheck_response("Running", fuseki)
        resp.content_type = 'application/json'
        resp.status = falcon.HTTP_200
        app_logger.info('Finished operations on /health GET Request.')
