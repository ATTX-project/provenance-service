import json
from prov.utils.queue import init_celery
from prov.utils.broker import broker
from prov.utils.messaging_client import RpcClient
from prov.applib.graph_store import GraphStore

app = init_celery(broker['user'], broker['pass'], broker['host'])


@app.task(name="construct.index", max_retries=5)
def index_task():
    """Parse Provenance Object and construct Provenance Graph."""
    prov = ProvenanceIndex(broker["framequeue"], broker["indexqueue"])
    result = prov._index_prov()
    return result


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
            return graph

    def _get_framed_provenance(self, graph):
        """Construct message for framing service."""
        message = dict()
        message["provenance"] = dict()
        message["payload"] = dict()
        payload_message = message["provenance"]

        payload_message["framingServiceInput"] = dict()
        payload_message["framingServiceInput"]["docType"] = "provenance"
        payload_message["framingServiceInput"]["ldFrame"] = ""
        payload_message["framingServiceInput"]["sourceData"] = []

        graph_data = dict({"inputType": "Graph", "input": str(graph)})
        payload_message["framingServiceInput"]["sourceData"].append(graph_data)

        frame_rpc = RpcClient(broker['host'], broker['user'], broker['pass'], broker['framequeue'])
        response = frame_rpc.call(message)
        return response

    def _do_bulk_index(self, frame_response):
        """Construct message for indexing service."""
        message = dict()
        message["provenance"] = dict()
        message["payload"] = dict()
        payload_message = message["provenance"]

        payload_message["indexingServiceInput"] = dict()
        payload_message["indexingServiceInput"]["task"] = "replace"
        payload_message["indexingServiceInput"]["targetAlias"] = ["alias"]
        payload_message["indexingServiceInput"]["sourceData"] = []

        frame_data = json.loads(frame_response)

        index_data = dict({"useBulk": True, "input": str(graph)})
        payload_message["indexingServiceInput"]["sourceData"].append(index_data)

        frame_rpc = RpcClient(broker['host'], broker['user'], broker['pass'], broker['framequeue'])
        response = frame_rpc.call(message)
        return response
