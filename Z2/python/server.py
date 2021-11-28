import socket
import threading


class Server:
    def __init__(self):
        self.protocol = "IPv4"
        self.server_properties = ("127.0.0.1", 8888)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(self.server_properties)

    def listen(self):
        while True:
            connection, address = self.server_socket.accept()
            with connection:
                print(f"Connection from: {address}", end='\t')
                while True:
                    message = connection.recv(BUFFER_SIZE)
                    if not message:
                        break
                    self.print_message(address, message)
                    connection.sendall(message)
            print("Connection closed by client.")

    @staticmethod
    def print_message(address, message):
        print(f"Received packet from {address[0]}:{address[1]}")
        print(f"Data: {message.decode('utf-8')}")
        print(f"Data size: {len(message)}")


class ServerV6(Server):
    def __init__(self):
        super().__init__()
        self.protocol = "IPv6"
        self.server_properties = ("127.0.0.1", 8888)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
        self.server_socket.bind(self.server_properties)


if __name__ == '__main__':
    PORT = 8888
    BUFFER_SIZE = 102400  # >65507

    server_v4 = Server()
    server_v6 = ServerV6()

    threading.Thread(target=server_v4.listen()).start()
    threading.Thread(target=server_v6.listen()).start()
