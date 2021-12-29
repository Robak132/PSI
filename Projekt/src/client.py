import socket
import struct
from typing import Tuple
from netaddr.ip import IPAddress
from message import Message, RequestMessage, ACKMessage, QuitMessage, MessageType


class Client:
    def __init__(self):
        self.SERVER_NOT_RESPONDING_TIMEOUT = 60  # After this time client will close connection

        self.recv_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.recv_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, False)
        self.recv_socket.bind(("::", 0))
        self.recv_socket.settimeout(self.SERVER_NOT_RESPONDING_TIMEOUT)
        self.recv_port = self.recv_socket.getsockname()[1]

        self.send_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.send_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, False)
        self.send_socket.bind(("::", 0))
        self.ack_port = None

    def receive(self, target_ip, messages):
        result = b""
        pkg_number = 0
        data_pkg_number = 0
        while True:
            binary_data = self.recv_socket.recv(448)
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
                self.send_message(ACKMessage(pkg_number), (target_ip, self.ack_port))
            if data_pkg_number == messages:
                self.send_message(QuitMessage(1), (target_ip, self.ack_port))
                break
        return result

    def send_message(self, message: Message, target: Tuple[str, int]):
        self.send_socket.sendto(message.pack(), target)

    def request(self, stream, target, messages=None):
        target = (str(IPAddress(target[0]).ipv6()), target[1])
        self.send_message(RequestMessage(stream, self.recv_port), target)
        return self.receive(target[0], messages)


if __name__ == '__main__':
    client = Client()
    data = client.request(stream=1, target=("127.0.0.1", 8801))
    print(data.decode("utf-8"))
