import logging
import threading

from client import ClientV4
from server import Server
from streams import Ping


def client_thread(receive_portV4, i: int):
    client = ClientV4(
        send_address=("127.0.0.1", 8800 + i),
        receive_address=("127.0.0.1", 8880 + i),
        logging_level=logging.DEBUG,
        turn_on_signals=False)
    result = client.request(1, ("127.0.0.1", receive_portV4), max_messages=10)
    assert "PING" * 10 == result.decode("utf-8")


if __name__ == '__main__':
    server = Server(logging_level=logging.DEBUG)
    server.register_stream(1, Ping(0.1))

    _, receive_portV4, *_ = server.ipv4_receive_address
    _, receive_portV6, *_ = server.ipv6_receive_address

    server.start()

    threads = []
    for i in range(1):
        thread = threading.Thread(target=lambda: client_thread(receive_portV4, i))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
    server.stop()
