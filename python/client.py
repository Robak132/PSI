import socket

if __name__ == '__main__':
    for messages in range(5):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.settimeout(1.0)
        message = b'Jakis tekst przykladowy'
        addr = ("127.0.0.1", 8888)

        client_socket.sendto(message, addr)