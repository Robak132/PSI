import logging
from threading import Thread

from client import ClientV4
from server import Server
from streams import Ping


def client_thread(receive_portV4, i: int):
    client = ClientV4(
        send_address=("127.0.0.1", 8800 + i),
        receive_address=("127.0.0.1", 8880 + i),
        logging_level=logging.CRITICAL,
        turn_on_signals=False)
    result = client.request(1, ("127.0.0.1", receive_portV4), max_messages=10)
    assert "PING" * 10 == result.decode("utf-8")


class Test8Connections:
    def test_8connections(self):
        server = Server(logging_level=logging.CRITICAL)
        server.register_stream(1, Ping(0.5))

        _, receive_portV4, *_ = server.ipv4_receive_address
        _, receive_portV6, *_ = server.ipv6_receive_address

        server.start()

        threads = []
        for i in range(1):
            thread = Thread(target=lambda: client_thread(receive_portV4, i))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()
        server.stop()
