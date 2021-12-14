import socket
import time
from message import Message


class Client:
    def __init__(self):
        self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_socket.bind(("127.0.0.1", 9900))
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_socket.bind(("127.0.0.1", 9999))
        self.protocol = "IPv4"

    def receive(self):
        full_data = b""
        while True:
            binary_data = self.recv_socket.recv(10240)
            if binary_data == b"END":
                break
            else:
                full_data += binary_data
            # time.sleep(1)
            print("Sending ACK")
            self.send_socket.sendto(b"ACK", ("127.0.0.1", 8800))
        print(f"{full_data.decode('utf-8')}")

    def send_message(self, message: bytes):
        self.send_socket.sendto(message, ("127.0.0.1", 8800))

    def request(self):
        self.send_message(Message(b"REQUEST").pack())
        self.receive()


if __name__ == '__main__':
    client = Client()
    client.request()
