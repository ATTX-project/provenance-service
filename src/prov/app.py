import falcon
from prov.utils.logs import app_logger
from prov.api.healthcheck import HealthCheck
from prov.api.provenance import ConstructProvenance, RetrieveProvenance
from prov.api.queues import RetrieveQueueTask
from prov.api.graph_endpoint import GraphStatistics, GraphList, ProvList
from prov.api.graph_endpoint import GraphResource, GraphSPARQL, GraphUpdate
from prov.api.index import IndexProv

api_version = "0.2"  # TO DO: Figure out a better way to do versioning


def init_api():
    """Create the API endpoint."""
    provservice = falcon.API()

    provservice.add_route('/health', HealthCheck())

    provservice.add_route('/%s/prov' % (api_version), ConstructProvenance())
    provservice.add_route('/%s/prov/show/{provID}' % (api_version), RetrieveProvenance())

    provservice.add_route('/%s/index/prov' % (api_version), IndexProv())

    provservice.add_route('/%s/status/task/{task_id}' % (api_version), RetrieveQueueTask())

    provservice.add_route('/%s/graph/query' % (api_version), GraphSPARQL())
    provservice.add_route('/%s/graph/update' % (api_version), GraphUpdate())
    provservice.add_route('/%s/graph/list' % (api_version), GraphList())
    provservice.add_route('/%s/graph/list/prov' % (api_version), ProvList())
    provservice.add_route('/%s/graph/statistics' % (api_version), GraphStatistics())
    provservice.add_route('/%s/graph' % (api_version), GraphResource())

    app_logger.info('ProvService REST API is running.')
    return provservice


# if __name__ == '__main__':
#     init_api()
