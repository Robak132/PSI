import threading

from src.streams import File
from src.server import Server
from src.client import Client


class TestServerClientConnection:
    def server_func(self):
        server = Server(10240)
        server.register_stream(1, File("tests/resources/test_file.txt"))
        server.start(max_connections=1)

    def test_client_server(self):
        server_thread = threading.Thread(target=self.server_func).start()
        client = Client()
        data = client.request(1)
        assert "1234567890\ntest\nzażółć gęsią jaźń" == data.decode("utf-8")

