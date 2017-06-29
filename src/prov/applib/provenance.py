# import json
import falcon
# from urlparse import urlparse
from prov.utils.logs import app_logger
# from prov.applib.update_prov import UpdateProv


class ConstructProvenance(object):
    """Update Provenance on request."""

    def on_post(self, req, resp):
        """Respond on GET request to map endpoint."""
        # modifiedSince = req.get_param('modifiedSince')
        # start = req.get_param_as_bool('start')
        # if req.get_param('wfapi') is not None:
        #     wf_host = urlparse(req.get_param('wfapi'))
        #     wf_endpoint = {'host': wf_host.hostname, 'port': wf_host.port, 'version': wf_host.path[1:]}
        # else:
        #     wf_endpoint = {'host': "localhost", 'port': 4301, 'version': "0.1"}
        # if req.get_param('graphStore') is not None:
        #     graph_host = urlparse(req.get_param('graphStore'))
        #     graph_store = {'host': graph_host.hostname, 'port': graph_host.port, 'dataset': graph_host.path[1:]}
        # else:
        #     graph_store = {'host': "localhost", 'port': 3030, 'dataset': "ds"}
        # # data = UpdateProv()
        # prov_args = [graph_store, wf_endpoint, modifiedSince, start]
        # # result = data.do_update(*prov_args)
        # resp.data = json.dumps(result)
        # resp.content_type = 'application/json'
        resp.status = falcon.HTTP_200
        app_logger.info('Finished operations on /prov GET Request.')


class RetrieveProvenance(object):
    """Update Provenance on request."""

    def on_post(self, req, resp):
        """Respond on GET request to map endpoint."""
        # modifiedSince = req.get_param('modifiedSince')
        # start = req.get_param_as_bool('start')
        # if req.get_param('wfapi') is not None:
        #     wf_host = urlparse(req.get_param('wfapi'))
        #     wf_endpoint = {'host': wf_host.hostname, 'port': wf_host.port, 'version': wf_host.path[1:]}
        # else:
        #     wf_endpoint = {'host': "localhost", 'port': 4301, 'version': "0.1"}
        # if req.get_param('graphStore') is not None:
        #     graph_host = urlparse(req.get_param('graphStore'))
        #     graph_store = {'host': graph_host.hostname, 'port': graph_host.port, 'dataset': graph_host.path[1:]}
        # else:
        #     graph_store = {'host': "localhost", 'port': 3030, 'dataset': "ds"}
        # # data = UpdateProv()
        # prov_args = [graph_store, wf_endpoint, modifiedSince, start]
        # # result = data.do_update(*prov_args)
        # resp.data = json.dumps(result)
        # resp.content_type = 'application/json'
        resp.status = falcon.HTTP_200
        app_logger.info('Finished operations on /prov GET Request.')
