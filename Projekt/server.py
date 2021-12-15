import socket
import struct
import threading
import time

from message import Message, DataMessage, QuitMessage

BUFFER = 400
HEADER = 7


class SendMessageThreadv2(threading.Thread):
    def __init__(self, timeout, send_socket, messages, address):
        super().__init__()
        self._stop = threading.Event()
        self.send_socket = send_socket
        self.messages = messages
        self.address = address
        self.timeout = timeout
        self.message_id = 0

        super().start()

    def run(self):
        print('run')
        # time.sleep(0.5)
        is_stopped = False
        while not is_stopped:
            message = DataMessage(self.message_id, self.messages[self.message_id])
            print(f"Package {self.message_id}/{len(self.messages)} sent")
            self.send_socket.sendto(message.pack(), self.address)
            is_stopped = self._stop.wait(0.005)

    def stop(self):
        self._stop.set()

    def next_message(self):
        self.message_id += 1


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
            messages = self.split_str(binary_data, segment_size)

            self.send_thread = SendMessageThreadv2(1, self.send_socket, messages, address)
            for i in range(len(messages)):
                self.wait_for_confirm(i)
                self.send_thread.next_message()
            self.send_thread.stop()

            print("Transmission ended", end="")
            self.send_socket.sendto(QuitMessage(1).pack(), address)

    def wait_for_confirm(self, packet_number):
        ACK_id = None
        while not ACK_id == packet_number:
            binary_data = self.recv_socket.recv(BUFFER_SIZE)
            message = Message.unpack(binary_data)
            if message.message_type == "ACK":
                ACK_id = message.identifier
        print(f"received ACK: {ACK_id}")

    def start(self):
        message_type = None
        address = None

        print(f"Waiting for client request")
        while message_type != "REQ":
            binary_data, address = self.recv_socket.recvfrom(BUFFER_SIZE)
            message_type = Message.unpack(binary_data).message_type
            pass

        print(f"Client request from {address[0]}:{address[1]}")
        self.send_file("file.txt", 400, ("127.0.0.1", 9900))


if __name__ == '__main__':
    BUFFER_SIZE = 10240  # >65507

    server = Server()
    server.start()
