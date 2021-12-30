import queue
import signal
import socket
import struct
import threading
import logging
from typing import Tuple
from message import Message, DataMessage, QuitMessage, InfoMessage, MessageType
from streams import File, Stream, Ping
from netaddr import IPAddress
import CONFIG as CFG


class CommunicationThread(threading.Thread):
    def __init__(self, stream: Stream, address, buffer_size, logger, server_address=('::', 0), interface=''):
        super().__init__()
        self.logger = logger

        self.CLIENT_NOT_RESPONDING_TIMEOUT = CFG.CLIENT_NOT_RESPONDING_TIMEOUT
        self.client_lag = 0

        self.NEXT_MESSAGE_TIMEOUT = CFG.NEXT_MESSAGE_TIMEOUT
        self.ACK_TIMEOUT = CFG.ACK_TIMEOUT

        server_address = (str(IPAddress(server_address[0]).ipv6()), 0)
        if interface is not None and interface != '':
            server_address = (server_address[0] + f'%{interface}', server_address[1])

        self.send_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.send_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, False)

        for address_info in socket.getaddrinfo(server_address[0], server_address[1]):
            if address_info[0].name == 'AF_INET6' and address_info[1].name == 'SOCK_DGRAM':
                server_address = address_info[4]
                break

        self.logger.debug(f'processed server_address: {server_address}')
        self.send_socket.bind(server_address)

        self.receive_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.receive_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, False)
        self.receive_socket.bind(server_address)
        self.receive_socket.settimeout(self.ACK_TIMEOUT)
        self.receive_port = self.receive_socket.getsockname()[1]

        self.stream = stream
        self.message_idx = 0
        self.address = address
        self.buffer_size = buffer_size
        self.client_connected = True

        self.stop_event = threading.Event()
        super().start()

    def stop(self):
        self.stop_event.set()

    def stopped(self):
        return self.stop_event.is_set()

    def get_next_message(self):
        try:
            # I'm trying to get next message
            data = self.stream.get_next_message(self.NEXT_MESSAGE_TIMEOUT)
            if data is not None:
                return DataMessage(self.message_idx, data)
            else:
                return None
        except queue.Empty:
            # There is no available message, I need to keep connection alive
            return DataMessage(self.message_idx)

    def run(self):
        message = InfoMessage(self.message_idx, self.receive_port)
        while not self.stopped():
            self.send_message(message, self.address)
            if self.confirm():
                break

        message = self.get_next_message()
        while not self.stopped() and message is not None and self.client_connected:
            self.send_message(message, self.address)
            if self.confirm():
                message = self.get_next_message()

        self.stream.close()
        self.logger.info("Transmission ended")
        if self.client_connected:
            self.send_message(QuitMessage(1), self.address)

    def send_message(self, message: Message, address: Tuple[str, int]):
        self.logger.debug(f"Send: {message}")
        self.send_socket.sendto(message.pack(), address)

    def confirm(self) -> bool:
        try:
            # Waiting for ACK
            binary_data = self.receive_socket.recv(self.buffer_size)
            message = Message.unpack(binary_data)
            if message.message_type == MessageType.ACK:
                ACK_id = message.identifier
                self.logger.debug(f"receive: {message}")
                if self.message_idx == ACK_id:
                    self.message_idx += 1
                    return True
            elif message.message_type == MessageType.FIN:
                self.logger.info("Client closed connection")
                self.client_connected = False
                return False

        except socket.timeout:
            # Timeout, I need to send another message
            # FIXME: Zrobić lepiej
            self.client_lag += self.ACK_TIMEOUT
            if self.client_lag >= self.CLIENT_NOT_RESPONDING_TIMEOUT:
                self.logger.info("Client not responding: timeout")
                self.client_connected = False
            return False


class StoppableThread(threading.Thread):
    """
    Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition.

    Based on: https://stackoverflow.com/questions/47912701/python-how-can-i-implement-a-stoppable-thread
    """

    def __init__(self, task):
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


class Server:
    def __init__(self, address=None, logging_level: int = logging.INFO, buffer_size=448):
        self.logger = self.setup_loggers(logging_level)
        self.setup_exit_handler()

        self.receive_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.receive_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, False)
        self.receive_socket.settimeout(1)

        self.interface = "ens33" if False else ""

        if address is None:
            address = ("::", 0)
        else:
            address = self.cast_address(address)

        self.receive_socket.bind(address)
        self.receive_address = self.receive_socket.getsockname()
        self.logger.info(f"Server bound on: {self.receive_address}")

        self.is_running = True
        self.buffer_size = buffer_size
        self.streams = {}
        self.threads = []

    @staticmethod
    def setup_loggers(logging_level: int):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging_level)
        log_format = '%(threadName)12s:%(levelname)8s %(message)s'
        stderr_handler = logging.StreamHandler()
        stderr_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(stderr_handler)
        return logger

    def cast_address(self, address: tuple[str, int]):
        ip_address, port = address
        ipV6_address = str(IPAddress(ip_address).ipv6())
        address = (ipV6_address, port)

        if self.interface:
            address = (ipV6_address + f"%{self.interface}", port)

        for socket_family, socket_type, _, _, socket_address in socket.getaddrinfo(*address):
            if socket_family.name == "AF_INET6" and socket_type.name == "SOCK_DGRAM":
                address = socket_address
                self.logger.debug(f"Cast address: {address}")
                return address

    def register_stream(self, idx: int, stream: Stream):
        self.streams[idx] = stream

    def stop(self):
        self.is_running = False
        for thread in self.threads:
            thread.stop()

    def setup_exit_handler(self):
        signal.signal(signal.SIGINT, lambda sig, frame: self.stop())

    def start(self, thread=True):
        if thread:
            thread = StoppableThread(self.receive)
            self.threads.append(thread)
        else:
            while self.is_running:
                self.receive()

    def receive(self):
        try:
            binary_data, address = self.receive_socket.recvfrom(self.buffer_size)
            message = Message.unpack(binary_data)
            if message.message_type == MessageType.REQ:
                self.logger.info(f"Client request from {address[0]}:{address[1]}, stream idx: {message.identifier}")
                receive_port = struct.unpack("i", message.data)[0]
                ip_address = address[0]

                if message.identifier in self.streams.keys():
                    self.logger.info(f"Sending stream {message.identifier} to {ip_address}:{receive_port}")
                    self.create_new_thread(message.identifier, (ip_address, receive_port))
                else:
                    self.logger.error(f"Error: stream doesn't exists.")
                    # TODO Send this error to client
        except socket.timeout:
            return

    def create_new_thread(self, stream_idx: int, address: tuple):
        stream = self.streams[stream_idx]
        stream.prepare()

        communication_thread = CommunicationThread(stream, address, self.buffer_size, self.logger,
                                                   self.receive_address, self.interface)
        self.threads.append(communication_thread)


if __name__ == '__main__':
    server = Server(('127.0.0.1', 8801), logging_level=logging.INFO)
    server.register_stream(1, File("resources/file.txt"))
    server.register_stream(2, Ping(1))
    server.start(thread=False)
