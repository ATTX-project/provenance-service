import requests
from os import environ
from urllib import quote
from prov.utils.logs import app_logger
from SPARQLWrapper import SPARQLWrapper
from requests.exceptions import ConnectionError


class GraphStore(object):
    """Handle requests to the Provenance Graph Store."""

    def __init__(self):
        """Check if we have everything to work with the Graph Store."""
        self.host = environ['GHOST'] if 'GHOST' in environ else "localhost"
        self.port = environ['GPORT'] if 'GPORT' in environ else "3030"
        self.dataset = environ['DS'] if 'DS' in environ else "ds"
        self.key = environ['GKEY'] if 'GKEY' in environ else "pw123"

        self.server_address = "http://{0}:{1}/$/".format(self.host, self.port)
        self.request_address = "http://{0}:{1}/{2}".format(self.host, self.port, self.dataset)

    def graph_health(self):
        """Do the Health check for Graph Store."""
        status = None
        try:
            request = requests.get("{0}ping".format(self.server_address))
        except Exception as error:
            app_logger.error('Something is wrong: {0}'.format(error))
            status = False
            raise ConnectionError('Tried getting graph health, with error {}'.format(error))
        else:
            app_logger.info('Response from Graph Store is {0}'.format(request))
            status = True
        return status

    def graph_list(self):
        """List Graph Store Named Graphs."""
        result = {}
        temp_list = []
        list_query = quote("select ?g (count(*) as ?count) {graph ?g {?s ?p ?o}} group by ?g")
        try:
            request = requests.get("{0}/sparql?query={1}".format(self.request_address, list_query))
        except Exception as error:
            app_logger.error('Something is wrong: {0}'.format(error))
            raise
        else:
            graphs = request.json()
            result['graphsCount'] = len(graphs['results']['bindings'])
            for g in graphs['results']['bindings']:
                temp_graph = dict([('graphURI', g['g']['value']), ('tripleCount', g['count']['value'])])
                temp_list.append(temp_graph)
            result['graphs'] = temp_list
            app_logger.info('Constructed list of Named graphs from "/{0}" dataset.'.format(self.dataset))
            return result

    def graph_statistics(self):
        """Graph Store statistics agregated."""
        result = {}
        try:
            request = requests.get("{0}stats/{1}".format(self.server_address, self.dataset), auth=('admin', self.key))
        except Exception as error:
            app_logger.error('Something is wrong: {0}'.format(error))
            raise
        else:
            stats = request.json()
            result['dataset'] = "/{0}".format(self.dataset)
            result['requests'] = {}
            result['requests']['totalRequests'] = stats['datasets']['/{0}'.format(self.dataset)]['Requests']
            result['requests']['failedRequests'] = stats['datasets']['/{0}'.format(self.dataset)]['RequestsBad']
            triples = 0
            graphs = self.graph_list()
            for e in graphs['graphs']:
                triples += int(e['tripleCount'])
            result['totalTriples'] = triples
            app_logger.info('Constructed statistics list for dataset: "/{0}".'.format(self.dataset))
            return result

    def graph_retrieve(self, named_graph):
        """Retrieve named graph from Graph Store."""
        try:
            request = requests.get("{0}/data?graph={1}".format(self.request_address, named_graph))
        except Exception as error:
            app_logger.error('Something is wrong: {0}'.format(error))
            raise
        else:
            if request.status_code == 200:
                app_logger.info('Retrived named graph: {0}.'.format(named_graph))
                return request.text
            elif request.status_code == 404:
                app_logger.info('Retrived named graph: {0} does not exist.'.format(named_graph))
                return None

    def graph_sparql(self, named_graph, query):
        """Execute SPARQL query on the Graph Store."""
        store_api = "{0}/query".format(self.request_address)
        try:
            sparql = SPARQLWrapper(store_api)
            # add a default graph, though that can also be in the query string
            sparql.addDefaultGraph(named_graph)
            sparql.setQuery(query)
            data = sparql.query().convert()
        except Exception as error:
            app_logger.error('Something is wrong: {0}'.format(error))
            raise
        else:
            app_logger.info('Execture SPARQL query on named graph: {0}.'.format(named_graph))
            return data.toxml()

    def graph_add(self, named_graph, data):
        """Update named graph in Graph Store."""
        headers = {'content-type': "text/turtle",
                   'cache-control': "no-cache"}
        try:
            request = requests.post("{0}/data?graph={1}".format(self.request_address, named_graph), data=data, headers=headers)
        except Exception as error:
            app_logger.error('Something is wrong: {0}'.format(error))
            raise
        else:
            app_logger.info('Updated named graph: {0}.'.format(named_graph))
            return request.json()

    def drop_graph(self, named_graph):
        """Drop named graph from Graph Store."""
        drop_query = quote(" DROP GRAPH <{0}>".format(named_graph))
        payload = "update={0}".format(drop_query)
        headers = {'content-type': "application/x-www-form-urlencoded",
                   'cache-control': "no-cache"}
        try:
            request = requests.post("{0}/update".format(self.request_address), data=payload, headers=headers)
        except Exception as error:
            app_logger.error('Something is wrong: {0}'.format(error))
            raise error
        else:
            app_logger.info('Deleted named graph: {0}.'.format(named_graph))
            return request.text
