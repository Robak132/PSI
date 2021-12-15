import socket
import struct
import threading
import time

from message import Message    

BUFFER = 128
HEADER = 7

class SendMessageThreadv2(threading.Thread):
    def __init__(self, timeout, send_socket, messages, address):
        super().__init__()
        self._stop = threading.Event()
        self.send_socket = send_socket
        self.messages = messages
        self.address = address
        self.timeout = timeout
        self.mes_number = 0

        super().start()

    def run(self):
        print('run')
        # time.sleep(0.5)
        is_stopped = False
        while not is_stopped:
            self.message = Message(b"MSG" + bytes(str(self.mes_number).ljust(4), 'utf-8'), self.messages[0], len(self.messages[0])).pack()
            print(f"Data no. {self.mes_number} sent [{len(self.message)}]")
            self.send_socket.sendto(self.message, self.address)
            is_stopped = self._stop.wait(0.02)

    def stop(self):
        self._stop.set()

    def next_message(self):
        self.mes_number += 1
        if len(self.messages) == 0:
            self.stop()
        else:
            self.messages.pop(0)

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

            len_segments = len(segments) - 1
            self.send_thread = SendMessageThreadv2(1, self.send_socket, segments, address)
            for i in range(len(segments)):
                print(f"Sending package {i}/{len_segments}")
                self.wait_for_confirm(i)
                self.send_thread.next_message()
            
            self.send_thread.stop()

            print("Transmission ended", end="")
            self.send_message(bytes("END", encoding="utf-8"), address)

    def send_str(self, message: str, address=("127.0.0.1", 9900)):
        self.send_message(message.encode("utf-8"), address)

    def send_message(self, message: bytes, address):
        self.send_socket.sendto(message, address)

    def wait_for_confirm(self, packet_number):
        binary_data = b''
        while not binary_data.decode('utf-8').startswith(f'ACK{packet_number}'):  # if packet_number is not None else ''
            print(f'expected: ACK{packet_number}')
            print(f"received: {binary_data.decode('utf-8')}")
            binary_data = self.recv_socket.recv(BUFFER_SIZE)
        print(f'expected: ACK{packet_number}')
        print(f"received: {binary_data.decode('utf-8')}")

    def start(self):
        message_type = None
        address = None

        print(f"Waiting for client request")
        while message_type != b"REQUEST":
            binary_data, address = self.recv_socket.recvfrom(BUFFER_SIZE)
            message_type = Message.unpack(binary_data, len(binary_data)).message_type

        print(f"Client request from {address[0]}:{address[1]}")
        self.send_file("file.txt", BUFFER - HEADER, ("127.0.0.1", 9900))


if __name__ == '__main__':
    BUFFER_SIZE = 10240  # >65507

    server = Server()
    server.start()
