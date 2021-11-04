import socket

SERVER_ADDRESS = "127.0.0.1"
SERVER_PORT = 8888

client_socket = None


def set_socket():
    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(1.0)


def send_messages():
    global client_socket
    if client_socket is None:
        raise ConnectionError('No client socket set.')

    for i in range(5):
        message = bytes(f"Message no. {i}", encoding="utf8")
        server = (SERVER_ADDRESS, SERVER_PORT)

        client_socket.sendto(message, server)


def main():
    set_socket()
    send_messages()


if __name__ == '__main__':
    main()
