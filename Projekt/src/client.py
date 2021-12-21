import socket
import struct

from src.message import Message, RequestMessage, ACKMessage, QuitMessage, MessageType


class Client:
    def __init__(self):
        self.SERVER_NOT_RESPONDING_TIMEOUT = 60  # After this time client will close connection

        self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_socket.bind(("", 9902))
        self.recv_socket.settimeout(self.SERVER_NOT_RESPONDING_TIMEOUT)

        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_socket.bind(("", 9992))
        self.ack_port = None
        self.protocol = "IPv4"

    def receive(self, messages):
        result = b""
        pkg_number = 0
        data_pkg_number = 0
        while True:
            binary_data = self.recv_socket.recv(10240)
            message = Message.unpack(binary_data)
            if message.message_type == MessageType.FIN:
                break
            if message.message_type == MessageType.INF:
                self.ack_port = struct.unpack("i", message.data)[0]
                print(f'Sending ACKs to: {self.ack_port}')
            elif message.message_type == MessageType.MSG and message.check_hash():
                if message.size != 0:
                    print(f'Received {message.message_type}: {message.identifier}')
                    if message.identifier == pkg_number + 1:
                        pkg_number += 1
                        data_pkg_number += 1
                        result += message.data
                else:
                    print(f'Received MSG (KEEP_ALIVE): {message.identifier}')
                    if message.identifier == pkg_number + 1:
                        pkg_number += 1

            if self.ack_port is not None:
                print(f"Sending ACK: {pkg_number}")
                self.send_socket.sendto(ACKMessage(pkg_number).pack(), ("127.0.0.1", self.ack_port))
            if data_pkg_number == messages:
                self.send_socket.sendto(QuitMessage(1).pack(), ("127.0.0.1", self.ack_port))
                break
        return result

    def send_message(self, message: bytes):
        self.send_socket.sendto(message, ("127.0.0.1", 8801))

    def request(self, stream, messages=None):
        self.send_message(RequestMessage(stream, 9902).pack())
        return self.receive(messages)


if __name__ == '__main__':
    client = Client()
    print(client.request(stream=1).decode("utf-8"))
