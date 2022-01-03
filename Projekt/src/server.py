import queue
import signal
import socket
import struct
import logging
from select import select
from time import time
from typing import Tuple
from message import Message, DataMessage, QuitMessage, InfoMessage, MessageType
from streams import File, Stream, Ping
from common import setup_loggers, StoppableThread
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

    def confirm(self) -> bool:
        try:
            while True:
                # Waiting for ACK
                message = self.receive_message()
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

    def send_message(self, message: Message, address: Tuple[str, int]):
        self.logger.debug(f"SEND: {message}")
        self.send_socket.sendto(message.pack(), address)

    def receive_message(self):
        binary_data = self.receive_socket.recv(self.buffer_size)
        message = Message.unpack(binary_data)
        lag = time() - message.timestamp
        self.logger.debug(f'RECV: {message}, lag = {lag:.2f}')
        return message

    def readjust_timeout(self, lag):
        if lag > self.SERVER_ACK_TIMEOUT:
            self.logger.info(f"Readjusting ACK timeout "
                             f"{self.SERVER_ACK_TIMEOUT}->{self.SERVER_ACK_TIMEOUT * 2}")
            self.SERVER_ACK_TIMEOUT *= 2
            self.receive_socket.settimeout(self.SERVER_ACK_TIMEOUT)


class CommunicationThreadV6(CommunicationThreadV4):
    def __init__(self,  **kwargs):
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
                 ipv4_address=("", 0),
                 ipv6_address=("", 0),
                 buffer_size=448,
                 logging_level: int = logging.INFO):
        self.logger = setup_loggers(logging_level)
        self.setup_exit_handler()

        self.sockets = []

        self.ipv4_receive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ipv4_receive_socket.settimeout(1)
        self.ipv4_receive_socket.bind(ipv4_address)
        self.ipv4_receive_address = self.ipv4_receive_socket.getsockname()
        self.logger.info(f"Server IPv4 bound on: {self.ipv4_receive_address}")
        self.sockets.append(self.ipv4_receive_socket)

        self.ipv6_receive_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.ipv6_receive_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, True)
        self.ipv6_receive_socket.settimeout(1)
        self.ipv6_receive_socket.bind(ipv6_address)
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

    def receive(self):
        ready_sockets, _, _ = select(self.sockets, [], [], 1)
        for ready_socket in ready_sockets:
            binary_data, address = ready_socket.recvfrom(self.buffer_size)
            message = Message.unpack(binary_data)
            if message.message_type == MessageType.REQ:
                self.logger.info(f"Client request from {address}, stream idx: {message.identifier}")
                receive_port = struct.unpack("i", message.data)[0]
                ip_address = address[0]

                if message.identifier in self.streams.keys():
                    self.logger.info(f"Sending stream {message.identifier} to {ip_address}:{receive_port}")
                    address = (ip_address, receive_port)
                    ip_version = IPAddress(ip_address).version
                    self.create_new_thread(message.identifier, address, ip_version)
                else:
                    self.logger.error(f"ERROR: stream doesn't exists.")
                    # TODO Send this error to client

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
    server = Server(ipv4_address=("127.0.0.1", 8801), logging_level=logging.DEBUG)
    server.register_stream(1, File("resources/file.txt"))
    server.register_stream(2, Ping(1))
    server.start(thread=False)