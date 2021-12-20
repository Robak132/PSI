import socket
import struct
import threading
import logging

from message import Message, DataMessage, QuitMessage, InfoMessage
from streams import File, Stream


class CommunicationThread(threading.Thread):
    def __init__(self, stream: Stream, address, buffer_size, logger):
        super().__init__()
        self.timeout = 1
        self.logger = logger

        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_socket.bind(('', 0))
        self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_socket.bind(('', 0))
        self.recv_socket.settimeout(self.timeout)

        self.steam = stream
        self.message_idx = 0
        self.message = self.steam.get_next_message()
        self.address = address
        self.buffer_size = buffer_size

        super().start()

    def run(self):
        recv_port = self.recv_socket.getsockname()[1]
        message = InfoMessage(self.message_idx, recv_port).pack()
        while True:
            self.send_socket.sendto(message, self.address)
            self.logger.debug(f"INFO sent [{self.message_idx}]")
            if self.confirm():
                break

        while self.message is not None:
            message = DataMessage(self.message_idx, self.message).pack()
            self.logger.debug(f"Data sent [{self.message_idx}]")
            self.send_socket.sendto(message, self.address)
            if self.confirm():
                self.message = self.steam.get_next_message()

        self.logger.info("Transmission ended")
        self.send_socket.sendto(QuitMessage(1).pack(), self.address)

    def confirm(self) -> bool:
        try:
            # Waiting for ACK
            binary_data = self.recv_socket.recv(self.buffer_size)
            message = Message.unpack(binary_data)
            if message.message_type == "ACK":
                ACK_id = message.identifier
                self.logger.debug(f"Received ACK: {ACK_id}")
                if self.message_idx == ACK_id:
                    self.message_idx += 1
                    return True
        except socket.timeout:
            # Timeout, I need to send another message
            return False


class Server:
    def __init__(self, buffer_size: int):
        self.logger = self.setup_loggers()

        self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_socket.bind(("127.0.0.1", 8801))
        self.send_thread = None

        self.streams = {}

        self.buffer_size = buffer_size

    @staticmethod
    def setup_loggers():
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
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

    def start(self):
        while True:
            self.logger.info(f"Waiting for client request")
            binary_data, address = self.recv_socket.recvfrom(self.buffer_size)
            message = Message.unpack(binary_data)
            if message.message_type == "REQ":
                self.logger.info(f"Client request from {address[0]}:{address[1]}, stream idx: {message.identifier}")
                recv_port = struct.unpack("i", message.data)[0]
                ip_address = address[0]

                if message.identifier in self.streams.keys():
                    self.logger.info(f"Sending stream {message.identifier} to {ip_address}:{recv_port}")
                    self.start_transmission(message.identifier, (ip_address, recv_port))
                else:
                    print(f"Error: stream doesn't exists.")
                    # TODO Send this error to client


if __name__ == '__main__':
    server = Server(10240)
    server.register_stream(1, File("../resources/file.txt"))
    server.start()
