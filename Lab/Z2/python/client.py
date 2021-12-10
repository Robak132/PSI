import socket
import threading
import time


class Client:
    def __init__(self, address, port, address_family=socket.AF_INET):
        self.protocol = "IPv4"
        self.socket_address = None
        self.client_socket = None
        self.connected = False
        self.prepare(address, port, address_family)

    def prepare(self, address, port, address_family):
        self.socket_address = (address, port)
        self.client_socket = socket.socket(address_family, socket.SOCK_STREAM)
        self.client_socket.settimeout(10.0)
        print(f"{self.protocol}: Trying to connect to: {self.socket_address}")
        try:
            self.client_socket.connect(self.socket_address)
            self.connected = True
        except socket.timeout:
            print(f"{self.protocol}: Connection ended: Timeout")
            self.connected = False

    def send_message(self, message: bytes):
        if self.connected:
            try:
                print(f"{self.protocol}: Sending {message}")
                self.client_socket.sendall(message)
            except OSError:
                pass

    def send_message_with_lag(self, message: bytes, t: int):
        if self.connected:
            self.send_message(message)
            print(f"{self.protocol}: Waiting for {t} s")
            time.sleep(t)

    def close(self):
        self.connected = False
        self.client_socket.shutdown(socket.SHUT_RDWR)
        self.client_socket.close()

    @staticmethod
    def create_message(size: int):
        message = bytes(f"{size}", encoding="utf8")
        message = message + b"\0" * (size - len(message))
        return message


class ClientV6(Client):
    def __init__(self, address, port, address_family=socket.AF_INET6):
        super().__init__(address, port, address_family)
        self.protocol = "IPv6"


if __name__ == '__main__':
    PORT = 8888

    client1 = Client("localhost", PORT)
    client1.send_message(b"1" * 500 + b"2" * 500)

    client2 = ClientV6("::1", PORT)
    client2.send_message(b"3" * 500 + b"4" * 500)

    client3 = Client("10.0.0.0", PORT)
    client3.send_message(b"1" * 500 + b"2" * 500)
