import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(('', 8888))

while True:
    message, address = server_socket.recvfrom(1024)
    message = message.decode('utf-8').upper()
    print(message)