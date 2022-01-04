import logging

from streams import File
from server import Server
from client import ClientV4WithLag


class TestLaggedConnection:
    def test_lagged_connection_ipv4(self):
        server = Server(logging_level=logging.CRITICAL)
        server.register_stream(1, File("tests/resources/test_file.txt"))

        _, receive_port, *_ = server.ipv4_receive_address

        server.start()

        client = ClientV4WithLag(logging_level=logging.CRITICAL, lag=0.5)
        data = client.request(1, ("127.0.0.1", receive_port))

        # Data send successfully
        assert "1234567890\r\ntest\r\nzażółć gęsią jaźń" == data.decode("utf-8")

        # Timeout was adjusted for client lag
        assert server.threads[0].SERVER_ACK_TIMEOUT == 4.096
        server.stop()
