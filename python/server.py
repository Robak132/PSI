import socket
import threading


def wrap_address(address):
    return f"Received packet from {address[0]}:{address[1]}"


def wrap_message(message):
    return f"Data: {message.decode('utf-8')}"


def create_new_thread_v4():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('', PORT))
    print("Server IPv4 is waiting for data...")
    while True:
        message, address = server_socket.recvfrom(BUFFER_SIZE)
        print(wrap_address(address))
        print(wrap_message(message))


def create_new_thread_v6():
    server_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    server_socket.bind(('', PORT))
    print("Server IPv6 is waiting for data...")
    while True:
        message, address = server_socket.recvfrom(BUFFER_SIZE)
        print(wrap_address(address))
        print(wrap_message(message))


if __name__ == '__main__':
    PORT = 8888
    BUFFER_SIZE = 1024

    threading.Thread(target=create_new_thread_v4).start()
    threading.Thread(target=create_new_thread_v6).start()
