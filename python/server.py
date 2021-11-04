import socket

def wrap_address(address):
    return f"Received packet from {address[0]}:{address[1]}"

def wrap_message(message):
    return f"Data: {message.decode('utf-8')}"

if __name__ == '__main__':
    PORT = 8888
    BUFFER_SIZE = 1024

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('', PORT))

    while True:
        print("Waiting for data...")
        message, address = server_socket.recvfrom(BUFFER_SIZE)
        print(wrap_address(address))
        print(wrap_message(message))