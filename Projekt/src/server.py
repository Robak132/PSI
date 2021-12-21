import queue
import socket
import struct
import threading
import logging

from src.message import Message, DataMessage, QuitMessage, InfoMessage, MessageType
from src.streams import File, Stream, Ping


class CommunicationThread(threading.Thread):
    def __init__(self, stream: Stream, address, buffer_size, logger):
        super().__init__()
        self.logger = logger

        self.NEXT_MESSAGE_TIMEOUT = 15  # How much time there is for new message to show up
        self.ACK_TIMEOUT = 1            # How much time client has for confirmation (ACK)

        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_socket.bind(('', 0))

        self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_socket.bind(('', 0))
        self.recv_socket.settimeout(self.ACK_TIMEOUT)
        self.recv_port = self.recv_socket.getsockname()[1]

        self.steam = stream
        self.message_idx = 0
        self.address = address
        self.buffer_size = buffer_size
        self.client_connected = True

        super().start()

    def get_next_message(self):
        try:
            # I'm trying to get next message
            data = self.steam.get_next_message(self.NEXT_MESSAGE_TIMEOUT)
            if data is not None:
                return DataMessage(self.message_idx, data)
            else:
                return None
        except queue.Empty:
            # There is no available message, I need to keep connection alive
            return DataMessage(self.message_idx)

    def run(self):
        message = InfoMessage(self.message_idx, self.recv_port).pack()
        while True:
            self.send_socket.sendto(message, self.address)
            self.logger.debug(f"INFO sent, idx={self.message_idx}, size={len(message)}")
            if self.confirm():
                break

        message = self.get_next_message()
        while message is not None and self.client_connected:
            self.logger.debug(f"Sending: {message}")
            self.send_socket.sendto(message.pack(), self.address)
            if self.confirm():
                message = self.get_next_message()

        self.steam.close()
        self.logger.info("Transmission ended")
        if self.client_connected:
            self.send_socket.sendto(QuitMessage(1).pack(), self.address)

    def confirm(self) -> bool:
        try:
            # Waiting for ACK
            binary_data = self.recv_socket.recv(self.buffer_size)
            message = Message.unpack(binary_data)
            if message.message_type == MessageType.ACK:
                ACK_id = message.identifier
                self.logger.debug(f"Received: {message}")
                if self.message_idx == ACK_id:
                    self.message_idx += 1
                    return True
            elif message.message_type == MessageType.FIN:
                self.client_connected = False
                return False

        except socket.timeout:
            # Timeout, I need to send another message
            return False


class Server:
    def __init__(self, address=None, buffer_size=10240):
        self.logger = self.setup_loggers()

        self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if address is None:
            self.recv_socket.bind(("", 0))
        else:
            self.recv_socket.bind(address)

        self.send_thread = None

        self.streams = {}

        self.buffer_size = buffer_size

    @staticmethod
    def setup_loggers():
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        log_format = '%(threadName)12s:%(levelname)8s %(message)s'
        stderr_handler = logging.StreamHandler()
        stderr_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(stderr_handler)
        return logger

    def start_transmission(self, stream_idx: int, address):
        stream = self.streams[stream_idx]
        stream.prepare()

        self.send_thread = CommunicationThread(stream, address, self.buffer_size, self.logger)
        self.send_thread.join()

    def register_stream(self, idx: int, stream: Stream):
        self.streams[idx] = stream

    def start(self, max_connections=None):
        connections = 0
        while connections != max_connections:
            self.logger.info(f"Waiting for client request")
            binary_data, address = self.recv_socket.recvfrom(self.buffer_size)
            message = Message.unpack(binary_data)
            if message.message_type == MessageType.REQ:
                self.logger.info(f"Client request from {address[0]}:{address[1]}, stream idx: {message.identifier}")
                recv_port = struct.unpack("i", message.data)[0]
                ip_address = address[0]

                if message.identifier in self.streams.keys():
                    self.logger.info(f"Sending stream {message.identifier} to {ip_address}:{recv_port}")
                    self.start_transmission(message.identifier, (ip_address, recv_port))
                else:
                    print(f"Error: stream doesn't exists.")
                    # TODO Send this error to client
            connections += 1


if __name__ == '__main__':
    server = Server(("127.0.0.1", 8801))
    server.register_stream(1, File("../resources/file.txt"))
    server.register_stream(2, Ping(1))
    server.start()
