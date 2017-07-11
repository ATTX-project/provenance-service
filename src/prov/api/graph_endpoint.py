import json
import falcon
from prov.utils.logs import app_logger
from prov.utils.graph_store import GraphStore


class GraphStatistics(object):
    """Construct Provenance based on provided request."""


class GraphList(object):
    """Update Provenance on request."""

    def on_get(self, req, resp):
        """Respond on GET request to map endpoint."""
        fuseki_graphs = GraphStore()
        resp.data = json.dumps(fuseki_graphs.graph_list(), indent=1, sort_keys=True)
        resp.content_type = 'application/json'
        resp.status = falcon.HTTP_200
        app_logger.info('Finished operations on /graph/list GET Request.')
