import socket

CONFIGURATION = {
    "ipv4": {
        "ip": "127.0.0.1",
        "port": 8888,
        "socket_inet": socket.AF_INET,
        "socket_dgram": socket.SOCK_DGRAM
    },
    "ipv6": {
        "ip": "::1",
        "port": 8888,
        "socket_inet": socket.AF_INET6,
        "socket_dgram": socket.SOCK_DGRAM
    }
}
client_socket = None


def send_message(message: bytes, server: tuple):
    size = len(message)
    try:
        client_socket.sendto(message, server)
        print(f"Successfully sent datagram of size {size}")
        return True
    except Exception as e:
        print(f"Failed to sent datagram of size {size}: {e}")
        return False


def create_message(size: int):
    message = bytes(f"{size}", encoding="utf8")
    message = message + b"\0" * (size - len(message))
    return message


def prepare_connection(use_ipv6=False):
    chosen_standard = "ipv6" if use_ipv6 else "ipv4"
    global client_socket

    client_socket = socket.socket(CONFIGURATION[chosen_standard]["socket_inet"],
                                  CONFIGURATION[chosen_standard]["socket_dgram"])
    client_socket.settimeout(1.0)

    server = (CONFIGURATION[chosen_standard]["ip"], CONFIGURATION[chosen_standard]["port"])
    return server


def test_different_message_sizes(use_ipv6=False):
    server = prepare_connection(use_ipv6)
    size = 1
    loop_is_running = True

    while loop_is_running:
        message = create_message(size=size)
        loop_is_running = send_message(message, server)
        if loop_is_running:
            size *= 2

    message = create_message(size=65507)
    send_message(message, server)


def main():
    test_different_message_sizes()
    test_different_message_sizes(use_ipv6=True)


if __name__ == '__main__':
    main()
