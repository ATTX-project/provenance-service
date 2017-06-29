# import json
import falcon
from prov.utils.logs import app_logger

# TO DO More detailed response from the health endpoint with statistics
# For now the endpoint responds with a simple 200


class HealthCheck(object):
    """Create HealthCheck class."""

    def on_get(self, req, resp):
        """Respond on GET request to map endpoint."""
        resp.status = falcon.HTTP_200  # implement 202 when it is needed
        app_logger.info('Finished operations on /health GET Request.')
