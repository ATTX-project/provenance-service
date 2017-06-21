import falcon
from prov.utils.logs import app_logger

api_version = "0.1"


class HealthCheck(object):
    """Create HealthCheck class."""

    def on_get(self, req, resp):
        """Respond on GET request to map endpoint."""
        resp.status = falcon.HTTP_200
        app_logger.info('Finished operations on /health GET Request.')


webapp = falcon.API()
webapp.add_route('/health', HealthCheck())
app_logger.info('App is running.')
