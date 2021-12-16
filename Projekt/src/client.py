import socket
from message import Message, RequestMessage, ACKMessage


class Client:
    def __init__(self):
        self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_socket.bind(("127.0.0.1", 9902))
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_socket.bind(("127.0.0.1", 9992))
        self.ack_port = None
        self.protocol = "IPv4"
        self._received_data = None

    def receive(self):
        full_data = b""
        pkg_number = 0
        while True:
            binary_data = self.recv_socket.recv(10240)
            message = Message.unpack(binary_data)
            print(message.message_type)
            if message.message_type == "FIN":
                break
            if message.message_type == "INF":
                print(f'Sending ACKs to: {message.data}')
                self.ack_port = int(message.data)
            elif message.message_type == 'MSG' and message.check_hash():
                print(f'Received {message.message_type}: {message.identifier}')
                if message.identifier == pkg_number + 1:
                    pkg_number += 1
                full_data += message.data
            print(f"Sending ACK: {pkg_number}")
            self.send_socket.sendto(ACKMessage(pkg_number).pack(), ("127.0.0.1", self.ack_port))
        self._received_data = full_data.decode('utf-8')
        print(full_data.decode('utf-8'))

    def send_message(self, message: bytes):
        self.send_socket.sendto(message, ("127.0.0.1", 8801))

    def request(self):
        self.send_message(RequestMessage(1).pack())
        self.receive()

    def get_received_data(self):
        return self._received_data


if __name__ == '__main__':
    client = Client()
    client.request()
