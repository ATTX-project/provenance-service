import json
from prov.utils.logs import app_logger
from prov.utils.queue import init_celery
from prov.utils.broker import broker
from prov.applib.messaging_client import RpcClient
from prov.applib.graph_store import GraphStore

app = init_celery(broker['user'], broker['pass'], broker['host'])
prov_alias = "attx"
prov_ld_frame = "{\"@type\": \"http:\/\/www.w3.org\/ns\/prov#Activity\"}"


@app.task(name="construct.index", max_retries=5)
def index_task():
    """Parse Provenance Object and construct Provenance Graph."""
    prov = ProvenanceIndex(broker["framequeue"], broker["indexqueue"])
    prov._index_prov()
    # return result


class ProvenanceIndex(object):
    """Indexing Provenance in Elasticsearch with an LD Frame."""

    def __init__(self, frame_queue, index_queue):
        """Initialize Provenance index."""
        self.frame_queue = frame_queue
        self.index_queue = index_queue

    def _index_prov(self):
        """Index provenance in Elasticsearch."""
        fuseki = GraphStore()
        data = fuseki._prov_list()
        for graph in data['graphs']:
            prov_doc_type = str(graph).split("http://data.hulib.helsinki.fi/prov_", 1)[1]
            bulk_framed = self._get_framed_provenance(graph, prov_doc_type)
            self._do_bulk_index(bulk_framed, prov_doc_type)
            app_logger.info('Indexed graph: {0} with doc type: {1}'.format(graph, prov_doc_type))

    def _get_framed_provenance(self, graph, prov_doc_type):
        """Construct message for framing service."""
        message = dict()
        message["provenance"] = dict()
        message["payload"] = dict()
        payload_message = message["payload"]

        payload_message["framingServiceInput"] = dict()
        payload_message["framingServiceInput"]["docType"] = prov_doc_type
        payload_message["framingServiceInput"]["ldFrame"] = prov_ld_frame
        payload_message["framingServiceInput"]["sourceData"] = []

        graph_data = dict({"inputType": "Graph", "input": str(graph)})
        payload_message["framingServiceInput"]["sourceData"].append(graph_data)

        frame_rpc = RpcClient(broker['host'], broker['user'], broker['pass'], broker['framequeue'])
        app_logger.info('Frame service message: {0}'.format(json.dumps(message)))
        response = frame_rpc.call(json.dumps(message))
        return response

    def _do_bulk_index(self, frame_response, prov_doc_type):
        """Construct message for indexing service."""
        message = dict()
        message["provenance"] = dict()
        message["payload"] = dict()
        payload_message = message["payload"]

        payload_message["indexingServiceInput"] = dict()
        payload_message["indexingServiceInput"]["task"] = "replace"
        payload_message["indexingServiceInput"]["targetAlias"] = [prov_alias]
        payload_message["indexingServiceInput"]["sourceData"] = []

        frame_data = json.loads(frame_response)

        if str(frame_data["payload"]["status"]).lower() == "success":
            frame_output = frame_data["payload"]["framingServiceOutput"]["output"]

            index_data = dict({"useBulk": True, "docType": prov_doc_type, "inputType": "URI", "input": str(frame_output)})
            payload_message["indexingServiceInput"]["sourceData"].append(index_data)

            frame_rpc = RpcClient(broker['host'], broker['user'], broker['pass'], broker['indexqueue'])
            app_logger.info('Index service message: {0}'.format(json.dumps(message)))
            response = frame_rpc.call(json.dumps(message))
            return response
        else:
            raise AssertionError("Frame operation did not succeed.")
