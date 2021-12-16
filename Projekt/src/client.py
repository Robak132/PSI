import socket
from message import Message, RequestMessage, ACKMessage


class Client:
    def __init__(self):
        self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_socket.bind(("127.0.0.1", 9900))
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_socket.bind(("127.0.0.1", 9999))
        self.protocol = "IPv4"

    def receive(self):
        full_data = b""
        pkg_number = 0
        while True:
            binary_data = self.recv_socket.recv(10240)
            message = Message.unpack(binary_data)
            if message.message_type == "FIN":
                break
            elif message.message_type == 'MSG':
                print(f'Received {message.message_type}: {message.identifier}')
                # Hash algorithm not working :C

                # hash_good = message.check_hash()
                # print(f'Data valid: {hash_good}')
                if message.identifier == pkg_number + 1:
                    pkg_number += 1
                full_data += message.data
            print(f"Sending ACK: {pkg_number}")
            self.send_socket.sendto(ACKMessage(pkg_number).pack(), ("127.0.0.1", 8800))
        print(full_data.decode('utf-8'))

    def send_message(self, message: bytes):
        self.send_socket.sendto(message, ("127.0.0.1", 8800))

    def request(self):
        self.send_message(RequestMessage(1).pack())
        self.receive()


if __name__ == '__main__':
    client = Client()
    client.request()
