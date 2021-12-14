import socket
import struct
import threading
import time

from message import Message


class SendMessageThread(threading.Thread):
    def __init__(self, timeout, send_socket, message, address):
        super().__init__()
        self._stop = threading.Event()
        self.send_socket = send_socket
        self.message = message
        self.address = address
        self.timeout = timeout

        super().start()

    def run(self):
        is_stopped = False
        while not is_stopped:
            print(f"Data sent [{len(self.message)}]")
            self.send_socket.sendto(self.message, self.address)
            is_stopped = self._stop.wait(self.timeout)

    def stop(self):
        self._stop.set()


class Server:
    def __init__(self):
        self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_socket.bind(("127.0.0.1", 8800))
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_socket.bind(("127.0.0.1", 8888))

        self.send_thread = None

        self.protocol = "IPv4"
        self.send_confirm = False

    @staticmethod
    def split_str(data: bytes, segment_size: int):
        return [data[i:i + segment_size] for i in range(0, len(data), segment_size)]

    def send_file(self, filename: str, segment_size: int, address):
        with open(filename, 'r', encoding='utf-8') as file:
            data = file.read()
            binary_data = bytes(data, encoding="utf-8")
            segments = self.split_str(binary_data, segment_size)

            for i in range(len(segments)):
                segment = segments[i]
                print(f"Sending package {i}/{len(segments)-1}")
                self.send_thread = SendMessageThread(1, self.send_socket, segment, address)
                self.wait_for_confirm()
                self.send_thread.stop()

            print("Transmission ended", end="")
            self.send_message(bytes("END", encoding="utf-8"), address)

    def send_str(self, message: str, address=("127.0.0.1", 9900)):
        self.send_message(message.encode("utf-8"), address)

    def send_message(self, message: bytes, address):
        self.send_socket.sendto(message, address)

    def wait_for_confirm(self):
        binary_data = None
        while binary_data != b"ACK":
            binary_data = self.recv_socket.recv(BUFFER_SIZE)
        print("ACK received\n")

    def start(self):
        message_type = None
        address = None

        print(f"Waiting for client request")
        while message_type != b"REQUEST":
            binary_data, address = self.recv_socket.recvfrom(BUFFER_SIZE)
            message_type = Message.unpack(binary_data).message_type

        print(f"Client request from {address[0]}:{address[1]}")
        self.send_file("file.txt", 128, ("127.0.0.1", 9900))


if __name__ == '__main__':
    BUFFER_SIZE = 10240  # >65507

    server = Server()
    server.start()
