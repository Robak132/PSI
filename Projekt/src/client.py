import logging
import signal
import socket
from time import time, sleep

from decorators import thread_request
from message import Message, RequestMessage, ACKMessage, QuitMessage, MessageType
from common import setup_loggers
import CONFIG as CFG


class ClientV4:
    def __init__(self,
                 receive_address: tuple[str, int] = ("", 0),
                 send_address: tuple[str, int] = ("", 0),
                 logging_level: int = logging.INFO):
        self.logger = setup_loggers(logging_level)
        self.setup_exit_handler()

        self.SERVER_NOT_RESPONDING_TIMEOUT = CFG.SERVER_NOT_RESPONDING_TIMEOUT
        self.CLIENT_ACK_TIMEOUT = CFG.CLIENT_ACK_TIMEOUT
        self.server_lag = 0

        self.receive_socket, self.receive_port, self.send_socket, self.send_port = self.setup_sockets(receive_address,
                                                                                                      send_address)
        self.target_ip = None
        self.ack_port = None
        self.is_running = True

    def setup_sockets(self, receive_address, send_address):
        receive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        receive_socket.bind(receive_address)
        receive_socket.settimeout(self.CLIENT_ACK_TIMEOUT)
        receive_port = receive_socket.getsockname()[1]

        send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        send_socket.bind(send_address)
        send_port = receive_socket.getsockname()[1]

        return receive_socket, receive_port, send_socket, send_port

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
                        self.is_running = False
                        break
                    elif message.message_type == MessageType.ERR:
                        self.logger.error(f"{message.data.decode('utf-8')}")
                        self.is_running = False
                        break
                    elif message.message_type == MessageType.INF:
                        ack_port = message.data_to_int()
                        if self.ack_port != ack_port:
                            self.ack_port = ack_port
                            self.logger.info(f'Sending ACKs to: {ack_port}')
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
                self.server_lag = self.server_lag + self.CLIENT_ACK_TIMEOUT
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

    def request(self, stream: int, target: tuple[str, int], thread: bool = False, max_messages: int = None):
        if thread:
            return self.request_thread(stream, target, max_messages)
        else:
            return self.request_blocking(stream, target, max_messages)

    def request_blocking(self, stream: int, target: tuple[str, int], max_messages: int = None):
        self.target_ip, _ = target
        self.send_message(RequestMessage(stream, self.receive_port), target)
        return self.receive(max_messages)

    @thread_request
    def request_thread(self, stream: int, target: tuple[str, int], max_messages: int = None):
        return self.request_blocking(stream, target, max_messages)


class ClientV6(ClientV4):
    def __init__(self,
                 receive_address: tuple[str, int] = ("", 0, 0, 0),
                 send_address: tuple[str, int] = ("", 0, 0, 0),
                 logging_level: int = logging.INFO):
        super().__init__(receive_address, send_address, logging_level)

    def setup_sockets(self, receive_address, send_address):
        receive_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        receive_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, True)
        receive_socket.bind(receive_address)
        receive_socket.settimeout(self.CLIENT_ACK_TIMEOUT)
        receive_port = receive_socket.getsockname()[1]

        send_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        send_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, True)
        send_socket.bind(send_address)
        send_port = receive_socket.getsockname()[1]

        return receive_socket, receive_port, send_socket, send_port


class ClientV4WithLag(ClientV4):
    def __init__(self, lag: float = 0, **kwargs):
        super().__init__(**kwargs)
        self.lag = lag

    def receive_message(self) -> Message:
        sleep(self.lag)
        return super().receive_message()

    def send_message(self, message: Message, target: tuple[str, int]):
        sleep(self.lag)
        super().send_message(message, target)


if __name__ == '__main__':
    client = ClientV4(logging_level=logging.DEBUG)
    data = client.request(stream=1, target=("127.0.0.1", 8801))
    # print(data.decode("utf-8"))
