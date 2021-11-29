import socket


class Client:
    def __init__(self):
        self.protocol = "IPv4"
        self.server = None
        self.client_socket = None
        self.prepare()

    def prepare(self):
        self.server = ("127.0.0.1", 8888)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(self.server)

    def send_message(self, message: bytes):
        size = len(message)
        try:
            self.client_socket.sendall(message)
            response = self.client_socket.recv(BUFFER_SIZE)
            return True
        except OSError:
            return False

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
        self.server = ("::1", 8889)
        self.client_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.client_socket.connect(self.server)


def main():
    # c = Client()
    # c.send_message(b"XDv4")

    c = ClientV6()
    c.send_message(b"XDv6")


if __name__ == '__main__':
    PORT = 8888
    BUFFER_SIZE = 102400  # >65507

    main()
