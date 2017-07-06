import falcon
from prov.utils.logs import app_logger
from prov.api.healthcheck import HealthCheck
from prov.api.provenance import ConstructProvenance, RetrieveProvenance

api_version = "0.1"  # TO DO: Figure out a better way to do versioning


def create():
    """Create the API endpoint."""
    do_prov = ConstructProvenance()
    get_prov = RetrieveProvenance()
    provservice = falcon.API()

    provservice.add_route('/health', HealthCheck())

    provservice.add_route('/%s/prov' % (api_version), do_prov)
    provservice.add_route('/%s/prov/show/{provID}' % (api_version), get_prov)

    # provservice.add_route('/%s/graph/query' % (api_version), do_sparql)
    # provservice.add_route('/%s/graph/update' % (api_version), do_graph_update)
    # provservice.add_route('/%s/graph/list' % (api_version), get_graph_list)
    # provservice.add_route('/%s/graph/statistics' % (api_version), get_graph_statistics)
    # provservice.add_route('/%s/graph/{graphID}' % (api_version), get_graph)

    app_logger.info('App is running.')
    return provservice


if __name__ == '__main__':
    create()
