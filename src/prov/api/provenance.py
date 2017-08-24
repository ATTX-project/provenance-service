import json
import falcon
from prov.schemas import load_schema
from prov.utils.validate import validate
from prov.utils.logs import app_logger
from prov.applib.construct_prov import construct_provenance


class ConstructProvenance(object):
    """Construct Provenance based on provided request."""

    @validate(load_schema('provschema'))
    def on_post(self, req, resp, parsed):
        """Respond on GET request to map endpoint."""
        response = construct_provenance.delay(parsed["provenance"], parsed["payload"])
        result = {'task_id': response.result}
        resp.body = json.dumps(result)
        resp.status = falcon.HTTP_200
        app_logger.info('Accepted POST Request for /prov.')


class RetrieveProvenance(object):
    """Update Provenance on request."""

    @validate(load_schema('idtype'))
    def on_get(self, req, resp, provID):
        """Respond on GET request to map endpoint."""
        resp.status = falcon.HTTP_200
        app_logger.info('Finished operations on /prov GET Request.')
