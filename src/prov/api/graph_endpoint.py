import json
import falcon
from prov.schemas import load_schema
from prov.utils.validate import validate
from prov.utils.logs import app_logger
from prov.applib.graph_store import GraphStore


class GraphStatistics(object):
    """Retrieve basic Graph Store statistics."""

    def on_get(self, req, resp):
        """Execution of the GET graph statistics request."""
        fuseki = GraphStore()
        resp.data = json.dumps(fuseki._graph_statistics(), indent=1, sort_keys=True)
        resp.content_type = 'application/json'
        resp.status = falcon.HTTP_200
        app_logger.info('Finished operations on /graph/statistics GET Request.')


class GraphList(object):
    """List named graphs in the graph store."""

    def on_get(self, req, resp):
        """Execution of the GET graph list request."""
        fuseki = GraphStore()
        resp.data = json.dumps(fuseki._graph_list(), indent=1, sort_keys=True)
        resp.content_type = 'application/json'
        resp.status = falcon.HTTP_200
        app_logger.info('Finished operations on /graph/list GET Request.')


class ProvList(object):
    """List named graphs in the graph store."""

    def on_get(self, req, resp):
        """Execution of the GET prov graph list request."""
        fuseki = GraphStore()
        resp.data = json.dumps(fuseki._prov_list(), indent=1, sort_keys=True)
        resp.content_type = 'application/json'
        resp.status = falcon.HTTP_200
        app_logger.info('Finished operations on /graph/list/prov GET Request.')


class GraphResource(object):
    """Retrieve or delete named graph."""

    def on_get(self, req, resp):
        """Execution of the GET named graph request."""
        graph_uri = req.get_param('uri')
        fuseki = GraphStore()
        response = fuseki._graph_retrieve(graph_uri)
        if response is not None:
            resp.data = str(response)
            resp.content_type = 'text/turtle'
            app_logger.info('Retrieved: {0}.'.format(graph_uri))
            resp.status = falcon.HTTP_200
        else:
            raise falcon.HTTPGone()

    def on_delete(self, req, resp):
        """Execution of the DELETE named graph request."""
        graph_uri = req.get_param('uri')
        fuseki = GraphStore()
        fuseki._drop_graph(graph_uri)
        resp.content_type = 'plain/text'
        app_logger.info('Deleted/DELETE graph with URI: {0}.'.format(graph_uri))
        resp.status = falcon.HTTP_200


# TO DO: Look into LD PATCH
class GraphUpdate(object):
    """Update Graph Store using a SPARQL Query."""

    @validate(load_schema('update'))
    def on_post(self, req, resp, parsed):
        """Execution of the POST update query request."""
        fuseki = GraphStore()
        resp.data = json.dumps(fuseki._graph_add(parsed['namedGraph'], parsed['triples']))
        resp.content_type = 'application/json'
        resp.status = falcon.HTTP_200
        app_logger.info('Finished operations on /graph/update POST Request.')


class GraphSPARQL(object):
    """Execute SPARQL Query on Graph Store."""

    @validate(load_schema('query'))
    def on_post(self, req, resp, parsed):
        """Execution of the POST SPARQL query request."""
        fuseki = GraphStore()
        data = fuseki._graph_sparql(parsed['namedGraph'], parsed['query'])
        resp.data = str(data)
        resp.content_type = 'application/xml'  # for now just this type
        resp.status = falcon.HTTP_200
        app_logger.info('Finished operations on /graph/query POST Request.')
