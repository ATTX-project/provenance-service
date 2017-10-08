import json
import falcon
from prov.utils.logs import app_logger
from prov.utils.graph_store import GraphStore
from amqpstorm.management import ApiConnectionError
from amqpstorm.management import ApiError
from amqpstorm.management import ManagementApi
from prov.utils.broker import broker

# TO DO More detailed response from the health endpoint with statistics
# For now the endpoint responds with a simple 200


def healthcheck_response(api_status, graph_health):
    """Content and format health status response."""
    health_status = dict([('provService', api_status)])
    if graph_health:
        health_status['graphStore'] = "Running"
    else:
        health_status['graphStore'] = "Not Running"
    API = ManagementApi(broker['host'], broker['user'], broker['pass'])
    try:
        result = API.aliveness_test('/')
        if result['status'] == 'ok':
            health_status['messageBroker'] = "Running"
        else:
            health_status['messageBroker'] = "Not Running"
    except ApiConnectionError as error:
        app_logger('Connection Error: %s' % error)
    except ApiError as error:
        app_logger('ApiError: %s' % error)
    return json.dumps(health_status, indent=1, sort_keys=True)


class HealthCheck(object):
    """Create HealthCheck class."""

    def on_get(self, req, resp):
        """Respond on GET request to map endpoint."""
        fuseki = GraphStore()
        # if you manange to call this it means the API is running
        resp.data = healthcheck_response("Running", fuseki.graph_health())
        resp.content_type = 'application/json'
        resp.status = falcon.HTTP_200
        app_logger.info('Finished operations on /health GET Request.')
