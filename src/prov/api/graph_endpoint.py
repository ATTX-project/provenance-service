import json
import falcon
from prov.utils.logs import app_logger
from prov.utils.graph_store import GraphStore


class GraphStatistics(object):
    """Construct Provenance based on provided request."""

    def on_get(self, req, resp):
        """Respond on GET request to map endpoint."""
        fuseki_graph = GraphStore()
        resp.data = json.dumps(fuseki_graph.graph_statistics(), indent=1, sort_keys=True)
        resp.content_type = 'application/json'
        resp.status = falcon.HTTP_200
        app_logger.info('Finished operations on /graph/statistics GET Request.')


class GraphList(object):
    """Update Provenance on request."""

    def on_get(self, req, resp):
        """Respond on GET request to map endpoint."""
        fuseki_graph = GraphStore()
        resp.data = json.dumps(fuseki_graph.graph_list(), indent=1, sort_keys=True)
        resp.content_type = 'application/json'
        resp.status = falcon.HTTP_200
        app_logger.info('Finished operations on /graph/list GET Request.')


class GraphResource(object):
    """Create Indexing Resource based on ID for retrieval."""

    def on_get(self, req, resp):
        """Respond on GET request to index endpoint."""
        graphURI = req.get_param('uri')
        fuseki_graph = GraphStore()
        response = fuseki_graph.retrieve_graph(graphURI)
        if response is not None:
            resp.data = str(response)
            resp.content_type = 'text/turtle'
            app_logger.info('Retrieved: {0}.'.format(graphURI))
            resp.status = falcon.HTTP_200
        else:
            raise falcon.HTTPGone()
            app_logger.warning('Retrieving: {0} is impossible graph does not exist or was deleted.'.format(graphURI))

    def on_delete(self, req, resp):
        """Respond on GET request to index endpoint."""
        graphURI = req.get_param('uri')
        fuseki_graph = GraphStore()
        fuseki_graph.drop_graph(graphURI)
        resp.content_type = 'plain/text'
        app_logger.info('Deleted/DELETE graph with URI: {0}.'.format(graphURI))
        resp.status = falcon.HTTP_200
