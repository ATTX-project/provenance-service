import requests
import os
from urllib import quote
# import falcon
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
        """Return Graph Store statistics."""
        result = {}
        temp_list = []
        list_query = quote("select ?g (count(*) as ?count) {graph ?g {?s ?p ?o}} group by ?g")
        try:
            request = requests.get("{0}sparql?query={1}".format(self.request_address, list_query))
        except Exception as error:
            raise error
        graphs = request.json()
        result['number'] = len(graphs['results']['bindings'])
        for g in graphs['results']['bindings']:
            temp_graph = dict([('graphURI', g['g']['value']), ('tripleCount', g['count']['value'])])
            temp_list.append(temp_graph)
        result['graphs'] = temp_list
        return result
