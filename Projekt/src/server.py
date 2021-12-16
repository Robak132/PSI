import socket
import threading

from message import Message, DataMessage, QuitMessage, InfoMessage
from data_provider import DataProvider


class CommunicationThread(threading.Thread):
    def __init__(self, binary_data, address, buffer_size):
        super().__init__()
        self.timeout = 1

        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_socket.bind(('', 0))
        self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_socket.bind(('', 0))
        self.recv_socket.settimeout(self.timeout)

        self.message_idx = 0
        self.messages = self.split_str(binary_data, 400)
        self.address = address
        self.buffer_size = buffer_size

        super().start()

    @staticmethod
    def split_str(data: bytes, segment_size: int):
        return [data[i:i + segment_size] for i in range(0, len(data), segment_size)]

    def run(self):
        while self.message_idx != len(self.messages):
            print(f"Data sent [{self.message_idx}/{len(self.messages)-1}]")
            message = DataMessage(self.message_idx, self.messages[self.message_idx]).pack()
            self.send_socket.sendto(message, self.address)
            self.confirm()
        print("Transmission ended", end="")
        self.send_socket.sendto(QuitMessage(1).pack(), self.address)

    def confirm(self):
        try:
            binary_data = self.recv_socket.recv(self.buffer_size)
            message = Message.unpack(binary_data)
            if message.message_type == "ACK":
                ACK_id = message.identifier
                print(f"Received ACK: {ACK_id}")
                if self.message_idx == ACK_id:
                    self.message_idx += 1
        except socket.timeout:
            return


class Server:
    def __init__(self, buffer_size: int):
        self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_socket.bind(("127.0.0.1", 8801))
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_socket.bind(("127.0.0.1", 8881))

        self.send_thread = None

        self.protocol = "IPv4"
        self.send_confirm = False

        self.buffer_size = buffer_size

    def send_file(self, filename: str, address):
        data_prov = DataProvider()
        data_prov.from_file(filename)
        data = data_prov.get_data()
        binary_data = bytes(data, encoding="utf-8")

        self.send_thread = CommunicationThread(binary_data, address, self.buffer_size)
        message = InfoMessage(1, str(self.send_thread.recv_socket.getsockname()[1]).encode('utf-8')).pack()
        print(self.send_thread.recv_socket.getsockname()[1])
        self.send_socket.sendto(message, address)
        self.send_thread.join()

    def start(self):
        message_type = None
        address = None

        print(f"Waiting for client request")
        while message_type != "REQ":
            binary_data, address = self.recv_socket.recvfrom(self.buffer_size)
            message_type = Message.unpack(binary_data).message_type

        print(f"Client request from {address[0]}:{address[1]}")
        self.send_file("../resources/file.txt", ("127.0.0.1", 9902))



if __name__ == '__main__':
    server = Server(10240)
    server.start()
