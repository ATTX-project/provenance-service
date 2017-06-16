import tornado.ioloop
import tornado.web


class MainHandler(tornado.web.RequestHandler):
    """Hellow world handler."""

    def get(self):
        """Handle get request."""
        self.write("Hello, world")


def make_app():
    """Start tornado app."""
    return tornado.web.Application([
        (r"/", MainHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
