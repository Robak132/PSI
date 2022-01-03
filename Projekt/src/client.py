import logging
import signal
import socket
import struct
from time import time, sleep
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
        self.logger = setup_loggers(logging_level)
        self.setup_exit_handler()

        self.SERVER_NOT_RESPONDING_TIMEOUT = CFG.SERVER_NOT_RESPONDING_TIMEOUT
        self.ACK_TIMEOUT = CFG.CLIENT_ACK_TIMEOUT
        self.server_lag = 0

        self.receive_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.receive_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, False)
        self.receive_socket.bind(receive_address)
        self.receive_socket.settimeout(self.ACK_TIMEOUT)
        self.receive_port = self.receive_socket.getsockname()[1]

        self.send_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.send_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, False)
        self.send_socket.bind(send_address)

        self.target_ip = None
        self.ack_port = None
        self.is_running = True

    def setup_exit_handler(self):
        signal.signal(signal.SIGINT, lambda sig, frame: self.stop())

    def stop(self):
        self.is_running = False

    def receive(self, max_messages: int = None):
        result = b""
        pkg_number = 0
        data_pkg_number = 0
        while self.is_running:
            try:
                while True:
                    message = self.receive_message()
                    if message.message_type == MessageType.FIN:
                        self.logger.info("Transmission ended")
                        break
                    elif message.message_type == MessageType.ERR:
                        self.logger.error(f"{message.data.decode('utf-8')}")
                        break
                    elif message.message_type == MessageType.INF:
                        self.ack_port = struct.unpack("i", message.data)[0]
                        self.logger.info(f'Sending ACKs to: {self.ack_port}')
                    elif message.identifier == pkg_number + 1 and message.message_type == MessageType.MSG and message.check_hash():
                        pkg_number += 1
                        self.server_lag = 0
                        if message.size != 0:
                            data_pkg_number += 1
                            result += message.data
                            if data_pkg_number == max_messages:
                                self.logger.info(f'Limit of received packages reached. Ending transmission.')
                                self.is_running = False
            except socket.timeout:
                self.server_lag = self.server_lag + self.ACK_TIMEOUT
                if self.server_lag >= self.SERVER_NOT_RESPONDING_TIMEOUT:
                    self.logger.info("Server not responding: timeout")
                    self.is_running = False

            if self.ack_port is not None:
                self.send_message(ACKMessage(pkg_number), (self.target_ip, self.ack_port))

        if not self.is_running and self.target_ip and self.ack_port:
            # Client is closing connection
            self.send_message(QuitMessage(1), (self.target_ip, self.ack_port))
        return result

    def receive_message(self) -> Message:
        binary_data = self.receive_socket.recv(448)
        message = Message.unpack(binary_data)
        lag = time() - message.timestamp
        self.logger.debug(f'RECV: {message}, lag = {lag:.2f}')
        return message

    def send_message(self, message: Message, target: tuple[str, int]):
        self.logger.debug(f'SEND: {message}')
        self.send_socket.sendto(message.pack(), target)

    def request(self, stream: int, target: tuple[str, int], max_messages: int = None):
        target = (str(IPAddress(target[0]).ipv6()), target[1])
        self.target_ip, _ = target
        self.send_message(RequestMessage(stream, self.receive_port), target)
        return self.receive(max_messages)


class ClientWithLag(Client):
    def __init__(self, lag: float = 0, **kwargs):
        super().__init__(**kwargs)
        self.lag = lag

    def receive_message(self) -> Message:
        sleep(self.lag)
        message = super().receive_message()
        return message

    def send_message(self, message: Message, target: tuple[str, int]):
        sleep(self.lag)
        super().send_message(message, target)


if __name__ == '__main__':
    client = ClientWithLag(logging_level=logging.DEBUG, lag=0.5)
    data = client.request(stream=1, target=("127.0.0.1", 8801))
    # print(data.decode("utf-8"))
