import socket


def send_messages():
    global client_socket
    if client_socket is None:
        raise ConnectionError('No client socket set.')

    size = 1
    loop_running = True
    while loop_running:
        message = bytes(f"{size}", encoding="utf8")
        message = message + b"\0" * (size - len(message))
        server = (SERVER_ADDRESS, SERVER_PORT)

        try:
            client_socket.sendto(message, server)
            print(f"Successfully sent datagram of size {size}")
            size = size * 2
        except Exception as e:
            print(f"Failed to sent datagram of size {size}: {e}")
            loop_running = False

    size = 65507
    message = bytes(f"{size}", encoding="utf8")
    message = message + b"\0" * (size - len(message))
    server = (SERVER_ADDRESS, SERVER_PORT)

    try:
        client_socket.sendto(message, server)
        print(f"Successfully sent datagram of size {size}")
    except Exception as e:
        print(f"Failed to sent datagram of size {size}: {e}")


def main():
    send_messages()


if __name__ == '__main__':
    SERVER_ADDRESS = "127.0.0.1"
    SERVER_PORT = 8888

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(1.0)
    main()
