import socket


class Client:
    def __init__(self):
        self.server = ("127.0.0.1", 8888)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.protocol = "IPv4"

    def send_message(self, message: bytes):
        size = len(message)
        try:
            self.client_socket.sendto(message, self.server)
            print(f"Successfully sent datagram of size {size}")
            return True
        except Exception as e:
            print(f"Failed to send datagram of size {size}")
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
        self.client_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.protocol = "IPv6"


def test_different_message_sizes(cls):
    size = 1
    loop_is_running = True

    client = cls()

    print(f"{' Doubling packet size every iteration ':*^80}\n")

    while loop_is_running:
        message = client.create_message(size=size)
        loop_is_running = client.send_message(message)
        if loop_is_running:
            size *= 2
        else:
            print(f"\nThe greatest length of a message described as a power of 2 equals {size // 2}")
            return size


def find_max_message_size(cls, minlen: int, maxlen: int):
    client = cls()

    print(f"\n{f' Looking for maximum message size for {client.protocol} ':*^80}\n")

    while maxlen - minlen > 1:
        testlen: int = int((minlen + maxlen) / 2)
        message = client.create_message(size=testlen)
        if client.send_message(message):
            minlen = testlen
        else:
            maxlen = testlen

    print(f"\nMaximum size of a message to send with {client.protocol} equals {minlen}\n")


def main():
    print(f"\n{' Client v4 ':#^80}\n")
    size = test_different_message_sizes(Client)
    find_max_message_size(Client, size/2, size)

    print(f"\n{' Client v6 ':#^80}\n")
    size = test_different_message_sizes(ClientV6)
    find_max_message_size(ClientV6, size/2, size)


if __name__ == '__main__':
    main()
