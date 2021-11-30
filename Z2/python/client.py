import socket


class Client:
    def __init__(self):
        self.protocol = "IPv4"
        self.socket_address = None
        self.client_socket = None
        self.prepare()

    def prepare(self):
        self.socket_address = ("localhost", 8888)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(self.socket_address)

    def send_message(self, message: bytes):
        size = len(message)
        try:
            self.client_socket.send(message)
            response = self.client_socket.recv(BUFFER_SIZE)
            print(response.decode('utf-8'))
        except OSError:
            pass

    def close(self):
        self.client_socket.shutdown(socket.SHUT_RDWR)
        self.client_socket.close()

    @staticmethod
    def create_message(size: int):
        message = bytes(f"{size}", encoding="utf8")
        message = message + b"\0" * (size - len(message))
        return message


class ClientV6(Client):
    def __init__(self):
        super().__init__()
        self.protocol = "IPv6"

    def prepare(self):
        self.socket_address = ("::1", 8888, 0, 0)
        self.client_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.client_socket.connect(self.socket_address)


def main():
    client = Client()
    client.send_message(b"XDv4")
    client.close()

    clientv6 = ClientV6()
    clientv6.send_message(b"XDv6")
    clientv6.close()


if __name__ == '__main__':
    PORT = 8888
    BUFFER_SIZE = 102400  # >65507

    main()
