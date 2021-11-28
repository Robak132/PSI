import socket


class Client:
    def __init__(self):
        self.protocol = "IPv4"
        self.server = ("127.0.0.1", 8888)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(self.server)

    def send_message(self, message: bytes):
        size = len(message)
        try:
            self.client_socket.sendall(message)
            response = self.client_socket.recv(1024)
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
        self.server = ("::1", 8888)
        self.client_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.protocol = "IPv6"


def main():
    pass


if __name__ == '__main__':
    main()
