import requests
import os
from urllib import quote
from prov.utils.logs import app_logger


class GraphStore(object):
    """Handle requests to the Provenance Graph Store."""

    def __init__(self):
        """Check if we have everything to work with the Graph Store."""
        try:
            self.host = os.environ['GHOST'] if 'GHOST' in os.environ else "localhost"
            self.port = os.environ['GPORT'] if 'GPORT' in os.environ else "3030"
            self.dataset = os.environ['DS'] if 'DS' in os.environ else "ds"
            self.key = os.environ['GKEY'] if 'GKEY' in os.environ else "pw123"

            self.server_address = "http://{0}:{1}/$/".format(self.host, self.port)
            self.request_address = "http://{0}:{1}/{2}/".format(self.host, self.port, self.dataset)
        except Exception as error:
            app_logger.error('Something is wrong: {0}'.format(error))
            raise error.message

    def graph_health(self):
        """Do the Health check for Graph Store."""
        try:
            request = requests.get("{0}ping".format(self.server_address))
        except Exception as error:
            app_logger.error('Something is wrong: {0}'.format(error))
            return False
        else:
            app_logger.info('Response from Graph Store is {0}'.format(request))
            return True

    def graph_list(self):
        """List Graph Store Named Graphs."""
        result = {}
        temp_list = []
        list_query = quote("select ?g (count(*) as ?count) {graph ?g {?s ?p ?o}} group by ?g")
        try:
            request = requests.get("{0}sparql?query={1}".format(self.request_address, list_query))
        except Exception as error:
            app_logger.error('Something is wrong: {0}'.format(error))
            raise error
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
            raise error
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

    def retrieve_graph(self, named_graph):
        """Drop named Graph from Graph Store."""
        try:
            request = requests.get("{0}data?graph={1}".format(self.request_address, named_graph))
        except Exception as error:
            app_logger.error('Something is wrong: {0}'.format(error))
            raise error
        if request.status_code == 200:
            # print request.text
            app_logger.info('Retrived named graph: {0}.'.format(named_graph))
            return request.text
        elif request.status_code == 404:
            app_logger.info('Retrived named graph: {0} does not exist.'.format(named_graph))
            return None

    def drop_graph(self, named_graph):
        """Drop named Graph from Graph Store."""
        drop_query = quote(" DROP GRAPH <{0}>".format(named_graph))
        payload = "update={0}".format(drop_query)
        headers = {'content-type': "application/x-www-form-urlencoded",
                   'cache-control': "no-cache"}
        try:
            request = requests.post("{0}update".format(self.request_address), data=payload, headers=headers)
        except Exception as error:
            app_logger.error('Something is wrong: {0}'.format(error))
            raise error
        app_logger.info('Deleted named graph: {0}.'.format(named_graph))
        return request.text
