import falcon
from prov.utils.logs import app_logger
from prov.applib.healthcheck import HealthCheck
from prov.applib.provenance import ConstructProvenance, RetrieveProvenance

api_version = "0.1"  # TO DO: Figure out a better way to do versioning


def create():
    """Create the API endpoint."""
    do_prov = ConstructProvenance()
    get_prov = RetrieveProvenance()
    provservice = falcon.API()

    provservice.add_route('/health', HealthCheck())
    provservice.add_route('/%s/prov' % (api_version), do_prov)
    provservice.add_route('/%s/prov/{provID}' % (api_version), get_prov)

    app_logger.info('App is running.')
    return provservice


if __name__ == '__main__':
    create()
