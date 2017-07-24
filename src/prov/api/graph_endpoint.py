import json
import falcon
from prov.schemas import load_schema
from prov.utils.validate import validate
from prov.utils.logs import app_logger
from prov.utils.graph_store import GraphStore


class GraphStatistics(object):
    """Retrieve basic Graph Store statistics."""

    def on_get(self, req, resp):
        """Execution of the GET graph statistics request."""
        fuseki = GraphStore()
        resp.data = json.dumps(fuseki.graph_statistics(), indent=1, sort_keys=True)
        resp.content_type = 'application/json'
        resp.status = falcon.HTTP_200
        app_logger.info('Finished operations on /graph/statistics GET Request.')


class GraphList(object):
    """List named graphs in the graph store."""

    def on_get(self, req, resp):
        """Execution of the GET graph list request."""
        fuseki = GraphStore()
        resp.data = json.dumps(fuseki.graph_list(), indent=1, sort_keys=True)
        resp.content_type = 'application/json'
        resp.status = falcon.HTTP_200
        app_logger.info('Finished operations on /graph/list GET Request.')


class GraphResource(object):
    """Retrieve or delete named graph."""

    def on_get(self, req, resp):
        """Execution of the GET named graph request."""
        graphURI = req.get_param('uri')
        fuseki = GraphStore()
        response = fuseki.retrieve_graph(graphURI)
        if response is not None:
            resp.data = str(response)
            resp.content_type = 'text/turtle'
            app_logger.info('Retrieved: {0}.'.format(graphURI))
            resp.status = falcon.HTTP_200
        else:
            raise falcon.HTTPGone()
            app_logger.warning('Retrieving: {0} is impossible graph does not exist or was deleted.'.format(graphURI))

    def on_delete(self, req, resp):
        """Execution of the DELETE named graph request."""
        graphURI = req.get_param('uri')
        fuseki = GraphStore()
        fuseki.drop_graph(graphURI)
        resp.content_type = 'plain/text'
        app_logger.info('Deleted/DELETE graph with URI: {0}.'.format(graphURI))
        resp.status = falcon.HTTP_200


# TO DO: Look into LD PATCH
class GraphUpdate(object):
    """Update Graph Store using a SPARQL Query."""

    @validate(load_schema('update'))
    def on_post(self, req, resp, parsed):
        """Execution of the POST update query request."""
        fuseki = GraphStore()
        resp.data = json.dumps(fuseki.graph_update(parsed['namedGraph'], parsed['triples']))
        resp.content_type = 'application/json'
        resp.status = falcon.HTTP_200
        app_logger.info('Finished operations on /graph/update POST Request.')


class GraphSPARQL(object):
    """Execute SPARQL Query on Graph Store."""

    @validate(load_schema('query'))
    def on_post(self, req, resp, parsed):
        """Execution of the POST SPARQL query request."""
        fuseki = GraphStore()
        data = fuseki.graph_sparql(parsed['namedGraph'], parsed['query'])
        resp.data = str(data)
        resp.content_type = 'application/xml'  # for now just this type
        resp.status = falcon.HTTP_200
        app_logger.info('Finished operations on /graph/query POST Request.')
