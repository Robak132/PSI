import logging
import socket
import struct
from netaddr.ip import IPAddress
from message import Message, RequestMessage, ACKMessage, QuitMessage, MessageType
from common import setup_loggers
import CONFIG as CFG


class Client:
    def __init__(self,
                 receive_address: tuple[str, int] = ("::", 0),
                 send_address: tuple[str, int] = ("::", 0),
                 *,
                 logging_level: int = logging.INFO):
        self.SERVER_NOT_RESPONDING_TIMEOUT = CFG.SERVER_NOT_RESPONDING_TIMEOUT

        self.logger = setup_loggers(logging_level)

        self.receive_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.receive_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, False)
        self.receive_socket.bind(receive_address)
        self.receive_socket.settimeout(self.SERVER_NOT_RESPONDING_TIMEOUT)
        self.receive_port = self.receive_socket.getsockname()[1]

        self.send_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.send_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, False)
        self.send_socket.bind(send_address)
        self.ack_port = None

    def receive(self, target_ip: str, max_messages: int = None):
        result = b""
        pkg_number = 0
        data_pkg_number = 0
        while True:
            binary_data = self.receive_socket.recv(448)
            message = Message.unpack(binary_data)
            if message.message_type == MessageType.FIN:
                break
            if message.message_type == MessageType.INF:
                self.ack_port = struct.unpack("i", message.data)[0]
                self.logger.debug(f'Sending ACKs to: {self.ack_port}')
            elif message.message_type == MessageType.MSG and message.check_hash():
                if message.size != 0:
                    self.logger.debug(f'Received {message.message_type}: {message.identifier}')
                    if message.identifier == pkg_number + 1:
                        pkg_number += 1
                        data_pkg_number += 1
                        result += message.data
                else:
                    self.logger.debug(f'Received MSG (KEEP_ALIVE): {message.identifier}')
                    if message.identifier == pkg_number + 1:
                        pkg_number += 1

            if self.ack_port is not None:
                self.logger.debug(f"Sending ACK: {pkg_number}")
                self.send_message(ACKMessage(pkg_number), (target_ip, self.ack_port))
            if data_pkg_number == max_messages:
                self.send_message(QuitMessage(1), (target_ip, self.ack_port))
                break
        return result

    def send_message(self, message: Message, target: tuple[str, int]):
        self.send_socket.sendto(message.pack(), target)

    def request(self, stream: int, target: tuple[str, int], max_messages: int = None):
        target = (str(IPAddress(target[0]).ipv6()), target[1])
        self.send_message(RequestMessage(stream, self.receive_port), target)
        return self.receive(target[0], max_messages)


if __name__ == '__main__':
    client = Client(logging_level=logging.INFO)
    data = client.request(stream=1, target=("127.0.0.1", 8801))
    print(data.decode("utf-8"))
