# Nazwa projektu: System niezawodnego strumieniowania danych po UDP
# Autorzy:        Michał Matak, Paweł Müller, Jakub Robaczewski, Grzegorz Rusinek
# Data:           14.01.2022

import signal
import socket
import logging
from queue import Empty
from select import select
from message import Message, DataMessage, QuitMessage, InfoMessage, MessageType, ErrorMessage, ErrorType
from streams import File, Stream, Ping
from common import setup_loggers, StoppableThread, send_message, receive_message, setup_sockets_ipv4, setup_sockets_ipv6
from netaddr import IPAddress
import CONFIG as CFG


class CommunicationThreadV4(StoppableThread):
    def __init__(self, stream: Stream, address, buffer_size, logger, server_ip_address="::"):
        self.logger = logger

        self.CLIENT_NOT_RESPONDING_TIMEOUT = CFG.CLIENT_NOT_RESPONDING_TIMEOUT
        self.NEXT_MESSAGE_TIMEOUT = CFG.NEXT_MESSAGE_TIMEOUT
        self.SERVER_ACK_TIMEOUT = CFG.SERVER_ACK_TIMEOUT
        self.client_lag = 0

        self.receive_socket, self.receive_port, self.send_socket, self.send_port = self.setup_sockets(server_ip_address)

        self.stream = stream
        self.message_idx = 0
        self.address = address
        self.buffer_size = buffer_size
        self.client_connected = True

        super().__init__()

    def setup_sockets(self, ip_address):
        receive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        receive_socket.bind((ip_address, 0))
        receive_socket.settimeout(self.SERVER_ACK_TIMEOUT)
        receive_port = receive_socket.getsockname()[1]

        send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        send_socket.bind((ip_address, 0))
        send_port = receive_socket.getsockname()[1]

        return receive_socket, receive_port, send_socket, send_port

    def get_next_message(self):
        try:
            # I'm trying to get next message
            data = self.stream.get_next_message(self.NEXT_MESSAGE_TIMEOUT)
            if data is not None:
                return DataMessage(self.message_idx, data)
            else:
                return None
        except Empty:
            # There is no available message, I need to keep connection alive
            return DataMessage(self.message_idx)

    def run(self):
        message = InfoMessage(self.message_idx, self.receive_port)
        while not self.stopped():
            send_message(self.send_socket, message, self.address, self.logger)
            if self.confirm():
                break

        message = self.get_next_message()
        while not self.stopped() and message is not None and self.client_connected:
            send_message(self.send_socket, message, self.address, self.logger)
            if self.confirm():
                message = self.get_next_message()

        self.stream.close()
        self.logger.info("Transmission ended")
        if self.client_connected:
            send_message(self.send_socket, QuitMessage(1), self.address, self.logger)

    def confirm(self) -> bool:
        try:
            while True:
                # Waiting for ACK
                message, _ = receive_message(self.receive_socket, self.buffer_size, self.logger)
                if message.message_type == MessageType.ACK:
                    ACK_id = message.identifier
                    if self.message_idx == ACK_id:
                        self.message_idx += 1
                        self.client_lag = 0
                        return True
                elif message.message_type == MessageType.FIN:
                    self.logger.info("Client closed connection")
                    self.client_connected = False
                    return False
        except socket.timeout:
            # Timeout, I need to send another message
            self.client_lag = self.client_lag + self.SERVER_ACK_TIMEOUT
            self.readjust_timeout(self.client_lag)
            if self.client_lag >= self.CLIENT_NOT_RESPONDING_TIMEOUT:
                self.logger.info("Client not responding: timeout")
                self.client_connected = False
            return False

    def readjust_timeout(self, lag):
        if lag > self.SERVER_ACK_TIMEOUT:
            self.logger.info(f"Readjusting ACK timeout "
                             f"{self.SERVER_ACK_TIMEOUT}->{self.SERVER_ACK_TIMEOUT * 2}")
            self.SERVER_ACK_TIMEOUT *= 2
            self.receive_socket.settimeout(self.SERVER_ACK_TIMEOUT)


class CommunicationThreadV6(CommunicationThreadV4):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def setup_sockets(self, ip_address):
        receive_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        receive_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, True)
        receive_socket.bind((ip_address, 0, 0, 0))
        receive_socket.settimeout(self.SERVER_ACK_TIMEOUT)
        receive_port = receive_socket.getsockname()[1]

        send_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        send_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, True)
        send_socket.bind((ip_address, 0, 0, 0))
        send_port = receive_socket.getsockname()[1]

        return receive_socket, receive_port, send_socket, send_port


class Server:
    def __init__(self,
                 ipv4_receive_address: tuple[str, int] = ("", 0),
                 ipv4_send_address: tuple[str, int] = ("", 0),
                 ipv6_receive_address: tuple[str, int, int, int] = ("", 0, 0, 0),
                 ipv6_send_address: tuple[str, int, int, int] = ("", 0, 0, 0),
                 buffer_size: int = 448,
                 logging_level: int = logging.INFO):
        self.logger = setup_loggers(logging_level)
        self.setup_exit_handler()

        self.sockets = []

        self.ipv4_receive_socket, self.ipv4_send_socket = setup_sockets_ipv4(ipv4_receive_address, 1, ipv4_send_address)
        self.ipv4_receive_address = self.ipv4_receive_socket.getsockname()
        self.logger.info(f"Server IPv4 bound on: {self.ipv4_receive_address}")
        self.sockets.append(self.ipv4_receive_socket)

        self.ipv6_receive_socket, self.ipv6_send_socket = setup_sockets_ipv6(ipv6_receive_address, 1, ipv6_send_address)
        self.ipv6_receive_address = self.ipv6_receive_socket.getsockname()
        self.logger.info(f"Server IPv6 bound on: {self.ipv6_receive_address}")
        self.sockets.append(self.ipv6_receive_socket)

        self.is_running = True
        self.main_thread = None
        self.buffer_size = buffer_size
        self.streams = {}
        self.threads = []

    def register_stream(self, idx: int, stream: Stream):
        self.streams[idx] = stream

    def stop(self):
        self.is_running = False
        if self.main_thread is not None:
            self.main_thread.stop()
        for thread in self.threads:
            thread.stop()

    def setup_exit_handler(self):
        signal.signal(signal.SIGINT, lambda sig, frame: self.stop())

    def start(self, thread=True):
        if thread:
            self.main_thread = StoppableThread(self.receive)
        else:
            while self.is_running:
                self.receive()

    def send_error(self, message: Message, address: tuple[str, int]):
        self.logger.debug(f"SEND: {message}")
        ip_version = IPAddress(address[0]).version
        send_socket = self.ipv4_send_socket if ip_version == 4 else self.ipv6_send_socket
        send_message(send_socket, message, address, self.logger)

    def receive(self):
        ready_sockets, _, _ = select(self.sockets, [], [], 1)
        for ready_socket in ready_sockets:
            message, address = receive_message(ready_socket, self.buffer_size, self.logger)
            if message.message_type == MessageType.REQ:
                self.logger.info(f"Client request from {address}, stream idx: {message.identifier}")
                ip_address, *_ = address
                address = (ip_address, message.data_to_int())
                ip_version = IPAddress(ip_address).version

                if message.identifier in self.streams.keys():
                    self.logger.info(f"Sending stream {message.identifier} to {address}")
                    self.create_new_thread(message.identifier, address, ip_version)
                else:
                    self.send_error(ErrorMessage(ErrorType.STREAM_NOT_FOUND), address)

    def create_new_thread(self, stream_idx: int, address: tuple, version: int):
        stream = self.streams[stream_idx]
        stream.prepare()

        if version == 4:
            communication_thread = CommunicationThreadV4(stream=stream,
                                                         address=address,
                                                         buffer_size=self.buffer_size,
                                                         logger=self.logger,
                                                         server_ip_address=self.ipv4_receive_address[0])
        else:
            communication_thread = CommunicationThreadV6(stream=stream,
                                                         address=address,
                                                         buffer_size=self.buffer_size,
                                                         logger=self.logger,
                                                         server_ip_address=self.ipv6_receive_address[0])
        self.threads.append(communication_thread)


if __name__ == '__main__':
    server = Server(ipv4_receive_address=("127.0.0.1", 8801), logging_level=logging.DEBUG)
    server.register_stream(1, File("resources/file.txt"))
    server.register_stream(2, Ping(1))
    server.start(thread=False)
