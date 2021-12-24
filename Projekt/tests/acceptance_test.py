import threading

from src.streams import File
from src.server import Server
from src.client import Client


class TestServerClientConnection:
    def test_client_server(self):
        server = Server(("127.0.0.1", 8888))
        server.register_stream(1, File("tests/resources/test_file.txt"))
        server.start()

        client = Client()
        data = client.request(1, ("127.0.0.1", 8888))
        assert "1234567890\ntest\nzażółć gęsią jaźń" == data.decode("utf-8")

        server.stop()
