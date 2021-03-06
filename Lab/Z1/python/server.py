import socket
import threading


def print_message(address, message):
    print(f"Received packet from {address[0]}:{address[1]}")
    print(f"Data: {message.decode('utf-8')}")
    print(f"Data size: {len(message)}")


def create_new_thread_v4():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('', PORT))
    print("Server IPv4 is waiting for data...")
    while True:
        message, address = server_socket.recvfrom(BUFFER_SIZE)
        print_message(address, message)


def create_new_thread_v6():
    server_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
    server_socket.bind(('', PORT))
    print("Server IPv6 is waiting for data...")
    while True:
        message, address = server_socket.recvfrom(BUFFER_SIZE)
        print_message(address, message)


if __name__ == '__main__':
    PORT = 8888
    BUFFER_SIZE = 102400  # >65507

    threading.Thread(target=create_new_thread_v4).start()
    threading.Thread(target=create_new_thread_v6).start()
