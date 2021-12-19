import socket
import struct
import threading

from message import Message, DataMessage, QuitMessage, InfoMessage
from streams import File, Stream


class CommunicationThread(threading.Thread):
    def __init__(self, stream: Stream, address, buffer_size):
        super().__init__()
        self.timeout = 1

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
        while self.message is not None:
            print(f"Data sent [{self.message_idx}]")
            message = DataMessage(self.message_idx, self.message).pack()
            self.send_socket.sendto(message, self.address)
            self.confirm()
        print("Transmission ended", end="")
        self.send_socket.sendto(QuitMessage(1).pack(), self.address)

    def confirm(self):
        try:
            # Waiting for ACK
            binary_data = self.recv_socket.recv(self.buffer_size)
            message = Message.unpack(binary_data)
            if message.message_type == "ACK":
                ACK_id = message.identifier
                print(f"Received ACK: {ACK_id}")
                if self.message_idx == ACK_id:
                    self.message_idx += 1
                    self.message = self.steam.get_next_message()
        except socket.timeout:
            # Timeout, I need to send another message
            return


class Server:
    def __init__(self, buffer_size: int):
        self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_socket.bind(("127.0.0.1", 8801))
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_socket.bind(("127.0.0.1", 8881))
        self.send_thread = None

        self.streams = {}

        self.buffer_size = buffer_size

    def start_transmission(self, stream_idx: int, address):
        stream = self.streams[stream_idx]

        self.send_thread = CommunicationThread(stream, address, self.buffer_size)
        message = InfoMessage(1, str(self.send_thread.recv_socket.getsockname()[1]).encode('utf-8')).pack()
        self.send_socket.sendto(message, address)
        self.send_thread.join()

    def register_stream(self, idx: int, stream: Stream):
        self.streams[idx] = stream

    def start(self):
        while True:
            print(f"Waiting for client request")
            binary_data, address = self.recv_socket.recvfrom(self.buffer_size)
            message = Message.unpack(binary_data)
            if message.message_type == "REQ":
                print(f"Client request from {address[0]}:{address[1]}")
                recv_port = struct.unpack("i", message.data)[0]
                ip_address = address[0]

                if message.identifier in self.streams.keys():
                    print(f"Sending stream to {ip_address}:{recv_port}")
                    self.start_transmission(message.identifier, (ip_address, recv_port))
                else:
                    print(f"Error: stream doesn't exists.")
                    # TODO Send this error to client


if __name__ == '__main__':
    server = Server(10240)
    server.register_stream(1, File("../resources/file.txt"))
    server.start()
