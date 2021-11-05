import socket


def send_messages():
    global client_socket
    if client_socket is None:
        raise ConnectionError('No client socket set.')

    for i in range(5):
        message = bytes(f"Message no. {i}", encoding="utf8")
        server = (SERVER_ADDRESS, SERVER_PORT)

        client_socket.sendto(message, server)


def main():
    send_messages()


if __name__ == '__main__':
    SERVER_ADDRESS = "127.0.0.1"
    SERVER_PORT = 8888

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(1.0)
    main()
