import json
import requests
import falcon
from os import environ
from prov.utils.logs import app_logger
from prov.applib.construct_index import index_task

ldframe = {'host': environ['FRAMEHOST'] if 'FRAMEHOST' in environ else "localhost",
           'api': environ['FRAMEVER'] if 'FRAMEVER' in environ else "0.2",
           'port': environ['FRAMEPORT'] if 'FRAMEPORT' in environ else 4303}

index = {'host': environ['INDEXHOST'] if 'INDEXHOST' in environ else "localhost",
         'api': environ['INDEXVER'] if 'INDEXVER' in environ else "0.2",
         'port': environ['INDEXPORT'] if 'INDEXPORT' in environ else 4304}


class IndexProv(object):
    """Index Provenance in Elasticsearch on request."""

    def on_post(self, req, resp):
        """POST request to index provenance documents in Elasticsearch."""
        try:
            response = execute_indexing()
            result = {'taskID': response.id}
            resp.body = json.dumps(result)
            resp.content_type = 'application/json'
            resp.status = falcon.HTTP_200
        except Exception:
            raise falcon.HTTPBadGateway(
                'Services not found',
                'Could not find Services for either ldFrame, esIndexing or both.'
            )
        app_logger.info('Accepted POST Request for /index/prov.')


def execute_indexing():
    """Index provenance data by applying ld frame."""
    try:
        frame_request = requests.get("http://{0}:{1}/health".format(ldframe["host"], ldframe["port"]))
        index_request = requests.get("http://{0}:{1}/health".format(index["host"], index["port"]))
        if frame_request.status_code == 200 and index_request.status_code == 200:
            response = index_task.delay()
    except Exception:
        app_logger.error('Could not find Services for either ldFrame, esIndexing or both.')
        pass
    else:
        return response
