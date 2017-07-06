import requests
# import os
import falcon


class GraphStore(object):
    """Handle requests to the Provenance Graph Store."""

    # TO BE REUSED LATER
    def __init__(self):
        """Check if we have everything to work with the Graph Store."""
        try:
            pass
            # os.environ['GHOST']
            # os.environ['GPORT']
            # os.environ['DS']
            # os.environ['GKEY']
        except Exception as e:
            raise e.message
        else:
            # self.host = os.environ['GHOST']
            # self.port = os.environ['GPORT']
            # self.dataset = os.environ['DS']
            # self.key = os.environ['KEY']

            self.host = "localhost"
            self.port = "3030"
            self.dataset = "ds"
            self.key = "pw123"
            self.server_address = "http://{0}:{1}/$/".format(self.host, self.port)
            self.request_address = "http://{0}:{1}/{2}/".format(self.host, self.port, self.dataset)

    def health(self):
        """Do the Health check for Graph Store."""
        try:
            r = requests.get("{0}ping".format(self.server_address))
        except Exception:
            raise falcon.HTTPBadRequest(
                'Invalid data',
                'Could not properly parse the provided data as JSON'
            )
        else:
            print r
            return True
