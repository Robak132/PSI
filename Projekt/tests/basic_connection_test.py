import logging

from streams import File
from server import Server
from client import ClientV4, ClientV6


class TestBasicConnectionV4:
    def test_basic_connection_ipv4(self):
        server = Server(logging_level=logging.CRITICAL)
        server.register_stream(1, File("tests/resources/test_file.txt"))
        _, receive_port, *_ = server.ipv4_receive_address

        server.start()

        client = ClientV4(logging_level=logging.CRITICAL)
        data = client.request(1, ("127.0.0.1", receive_port))
        assert "1234567890\ntest\nzażółć gęsią jaźń" == data.decode("utf-8")

        server.stop()


class TestBasicConnectionV6:
    def test_basic_connection_ipv6(self):
        server = Server(ipv6_address=("::1", 8888), logging_level=logging.CRITICAL)
        server.register_stream(1, File("tests/resources/test_file.txt"))

        _, receive_port, *_ = server.ipv6_receive_address

        server.start()

        client = ClientV6(logging_level=logging.CRITICAL)
        data = client.request(1, ("::1", receive_port))
        assert "1234567890\ntest\nzażółć gęsią jaźń" == data.decode("utf-8")

        server.stop()


class TestTwinConnection:
    def test_basic_connection_both_ip(self):
        server = Server(logging_level=logging.CRITICAL)
        server.register_stream(1, File("tests/resources/test_file.txt"))

        _, receive_portV4, *_ = server.ipv4_receive_address
        _, receive_portV6, *_ = server.ipv6_receive_address

        server.start()

        clientV4 = ClientV4(logging_level=logging.CRITICAL)
        data = clientV4.request(1, ("127.0.0.1", receive_portV4))
        assert "1234567890\ntest\nzażółć gęsią jaźń" == data.decode("utf-8")

        clientV6 = ClientV6(logging_level=logging.CRITICAL)
        data = clientV6.request(1, ("::1", receive_portV6))
        assert "1234567890\ntest\nzażółć gęsią jaźń" == data.decode("utf-8")

        server.stop()
