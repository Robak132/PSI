import socket


class Client:
    def __init__(self):
        self.server = ("127.0.0.1", 8888)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_message(self, message: bytes):
        size = len(message)
        try:
            self.client_socket.sendto(message, self.server)
            print(f"Successfully sent datagram of size {size}")
            return True
        except Exception as e:
            print(f"Failed to send datagram of size {size}: {e}")
            return False

    @staticmethod
    def create_message(size: int):
        message = bytes(f"{size}", encoding="utf8")
        message = message + b"\0" * (size - len(message))
        return message


class ClientV6(Client):
    def __init__(self):
        self.server = ("::1", 8888)
        self.client_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        super().__init__()


def test_different_message_sizes(cls):
    size = 1
    loop_is_running = True

    client = cls()

    while loop_is_running:
        message = client.create_message(size=size)
        loop_is_running = client.send_message(message)
        if loop_is_running:
            size *= 2

    message = client.create_message(size=65507)
    client.send_message(message)


def main():
    test_different_message_sizes(Client)
    test_different_message_sizes(ClientV6)


if __name__ == '__main__':
    main()
