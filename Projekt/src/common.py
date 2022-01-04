import logging
import threading
from _socket import IPPROTO_IPV6, IPV6_V6ONLY
from socket import socket, AF_INET, SOCK_DGRAM, AF_INET6
from message import Message
from time import time


class StoppableThread(threading.Thread):
    """
    Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition.

    Based on: https://stackoverflow.com/questions/47912701/python-how-can-i-implement-a-stoppable-thread
    """

    def __init__(self, task=None):
        super().__init__()
        self._stop_event = threading.Event()
        self.task = task
        self.start()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        while not self.stopped():
            self.task()


def setup_sockets_ipv4(receive_address, receive_timeout, send_address):
    receive_socket = socket(AF_INET, SOCK_DGRAM)
    receive_socket.bind(receive_address)
    receive_socket.settimeout(receive_timeout)

    send_socket = socket(AF_INET, SOCK_DGRAM)
    send_socket.bind(send_address)

    return receive_socket, send_socket


def setup_sockets_ipv6(receive_address, receive_timeout, send_address):
    receive_socket = socket(AF_INET6, SOCK_DGRAM)
    receive_socket.setsockopt(IPPROTO_IPV6, IPV6_V6ONLY, True)
    receive_socket.bind(receive_address)
    receive_socket.settimeout(receive_timeout)

    send_socket = socket(AF_INET6, SOCK_DGRAM)
    send_socket.setsockopt(IPPROTO_IPV6, IPV6_V6ONLY, True)
    send_socket.bind(send_address)

    return receive_socket, send_socket


def send_message(send_socket: socket, message: Message, address: tuple[str, int], logger):
    logger.debug(f"SEND: {message}")
    send_socket.sendto(message.pack(), address)


def receive_message(receive_socket: socket, logger) -> tuple[Message, tuple[str, int]]:
    binary_data, address = receive_socket.recvfrom(Message.MAX_MESSAGE_SIZE)
    message = Message.unpack(binary_data)
    logger.debug(f'RECV: {message}, lag = {time() - message.timestamp:.2f}')
    return message, address


def setup_loggers(logging_level: int):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging_level)
    log_format = '%(threadName)12s:%(levelname)8s %(message)s'
    stderr_handler = logging.StreamHandler()
    stderr_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(stderr_handler)
    return logger
