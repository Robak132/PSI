import threading
import socket
import time


class Server:
    def __init__(self, address, port, protocol_name="IPv4"):
        self.protocol = protocol_name
        self.server_socket = self.setup_sockets(address, port)
        self.server_socket.listen(1)
        print(f"{self.protocol}: Opened socket connection: {self.server_socket}")

    def setup_sockets(self, address, port):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((address, port))
        server_socket.settimeout(10)
        return server_socket

    def run(self):
        while True:
            try:
                connection, address = self.server_socket.accept()
                with connection:
                    print(f'{self.protocol}: Connected by {address}')
                    while True:
                        data = connection.recv(BUFFER_SIZE)
                        if not data:
                            break
                        self.print_message(address, data)
                    connection.close()
                print(f'{self.protocol}: Connection with {address} ended')
            except socket.timeout:
                print(f'{self.protocol}: Connection ended: Timeout')
                break

    def print_message(self, address, message):
        print(f"{self.protocol}: Received message: {message.decode('utf-8')}"
              f"[{len(message)}] from {address[0]}:{address[1]}")


class ServerV6(Server):
    def __init__(self, address, port):
        super().__init__(address, port, protocol_name="IPv6")

    def setup_sockets(self, address, port):
        server_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((address, port, 0, 0))
        server_socket.settimeout(10)
        return server_socket


if __name__ == '__main__':
    BUFFER_SIZE = 100
    try:
        threading.Thread(target=Server("127.0.0.1", 8888).run).start()
        threading.Thread(target=ServerV6("::1", 8888).run).start()
    except Exception as e:
        print(f"Error occurred: {e}")
