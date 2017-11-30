import click
import unittest
from prov.app import init_api
from click.testing import CliRunner
from prov.provservice import PROVService, number_of_workers, main, consumer
from mock import patch
# import mock
from prov.applib.messaging import Consumer


class TestService(unittest.TestCase):
    """Test app is ok."""

    def setUp(self):
        """Set up test fixtures."""
        self.host = '127.0.0.1'
        self.workers = number_of_workers()
        self.port = 7030
        self.log = 'logs/server.log'
        options = {
            'bind': '{0}:{1}'.format(self.host, self.port),
            'workers': self.workers,
            'daemon': 'True',
            'errorlog': self.log
        }
        self.app = PROVService(init_api(), options)
        # propagate the exceptions to the test client
        self.app.testing = True

    def tearDown(self):
        """Tear down test fixtures."""
        pass

    def test_command(self):
        """Test Running from command line."""
        @click.command("server")
        @click.option('--host')
        def server(host):
            click.echo('{0}'.format(host))

        runner = CliRunner()
        result = runner.invoke(server, input=self.host)
        assert not result.exception

    @patch.object(Consumer, 'start')
    def test_command_consumer(self, mock):
        """Test Running consumer from command line."""
        runner = CliRunner()
        result = runner.invoke(consumer)
        assert not result.exception

    def running_app(self):
        """Test running app."""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 404)

    @patch('prov.provservice.cli')
    def test_cli(self, mock):
        """Test if cli was called."""
        main()
        self.assertTrue(mock.called)


if __name__ == "__main__":
    unittest.main()
