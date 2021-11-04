import socket

if __name__ == '__main__':
    PORT = 8888
    BUFFER_SIZE = 1024

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('', PORT))

    while True:
        message, address = server_socket.recvfrom(BUFFER_SIZE)
        print(message.decode('utf-8').upper())